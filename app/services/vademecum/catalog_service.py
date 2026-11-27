# -*- coding: utf-8 -*-
# app/services/vademecum/catalog_service.py
"""Catálogo público de fichas (API-13, GES-03).

Solo fichas `published` y sin borrar. Nunca expone la ruta ni el enlace del PDF: la descarga
es un POST con sesión (API-14). Las imágenes que se publican son la miniatura y la vista
previa de baja resolución que genera API-10.
"""

import calendar
import math
import os
import re
import unicodedata
from datetime import datetime, timedelta

from bson import ObjectId
from bson.errors import InvalidId

from app.models.vademecum import (
    VademecumArea, VademecumRating, VademecumSheet, VademecumSheetType, VademecumSiteContent)
from app.models.vademecum.constants import GRADE_LABELS, GRADES

SORTS = {
    "newest": ("-publishedAt", "-id"),
    "number": ("sheetType", "number"),
    "popular": ("-downloadCount", "-publishedAt"),
}
# Estos dos se calculan en el servidor (decisión 0.5): los enviaba la web.
AGG_SORTS = ("rating", "commented")
NEW_SHEET_WINDOW_DAYS = 30
HOME_SIZE = 8
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MAX_QUERY_LENGTH = 100
# Campos que el listado necesita: deja fuera searchText, sourcePages y rutas de archivos
SUMMARY_FIELDS = ("id", "code", "number", "title", "description", "sheetType", "grades", "areas",
                  "publishedAt", "fileReplacedAt", "downloadCount", "ratingCount", "ratingSum",
                  "file.pageCount", "file.thumbnailPath", "file.previewPath")


def invalid(field, msg="Invalid field"):
    return {field: [{"status": "1", "msg": msg}]}, 400


def not_found():
    return {"general": [{"status": "5", "msg": "Record not found"}]}, 404


def isoformat(value):
    return value.replace(microsecond=0).isoformat() + "Z" if value else None


def object_id(value):
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError):
        return None


def truthy(value):
    """Los filtros booleanos de query aceptan `1`, `true` o `yes`."""
    return str(value or "").strip().lower() in ("1", "true", "yes")


def image_url(sheet, kind):
    """URL pública de la imagen con ?v= para invalidar caché, o None si no existe."""
    path = sheet.file and (sheet.file.thumbnailPath if kind == "thumbnail"
                           else sheet.file.previewPath)
    if not path:
        return None
    version = sheet.fileReplacedAt or sheet.publishedAt
    suffix = "?v={}".format(calendar.timegm(version.utctimetuple())) if version else ""
    return "/vademecum/sheets/{}/{}.webp{}".format(sheet.id, kind, suffix)


# Código de ficha escrito por el docente: "HT-41", "ht41", "HT4" (empieza por). Prefijo de 2 a 4
# letras y al menos una cifra (una palabra sola sigue yendo a la búsqueda de texto)
CODE_QUERY = re.compile(r"^(?P<prefix>[A-Za-z]{2,4})(?P<rest>-?\d[\d-]{0,7})$")


def code_query(q):
    """Filtro Mongo por código si `q` parece un código de ficha; None si es texto."""
    match = CODE_QUERY.match(q.replace(" ", ""))
    if not match:
        return None
    prefix, rest = match.group("prefix").upper(), match.group("rest")
    patterns = ["^" + re.escape(prefix + rest)]
    if "-" not in rest:
        # "HT41" también es "HT-41": el guion es opcional al buscar
        patterns.append("^" + re.escape(prefix + "-" + rest))
    return {"$or": [{"code": {"$regex": pattern, "$options": "i"}} for pattern in patterns]}


ACCENT_CLASSES = {
    u"a": u"[aáàäâ]",
    u"e": u"[eéèëê]",
    u"i": u"[iíìïî]",
    u"o": u"[oóòöô]",
    u"u": u"[uúùüû]",
    u"n": u"[nñ]",
}


def accent_insensitive_pattern(token):
    """Regex que ignora tildes/diéresis y mayúsculas (p. ej. 'balan' matchea 'Balanza')."""
    if isinstance(token, bytes):
        token = token.decode("utf-8", "ignore")
    normalized = unicodedata.normalize("NFD", token).lower()
    parts = []
    for ch in normalized:
        if unicodedata.category(ch) == "Mn":
            continue
        parts.append(ACCENT_CLASSES.get(ch, re.escape(ch)))
    return u"".join(parts)


def partial_text_query(q):
    """Filtro Mongo parcial sobre título, descripción y código cuando `$text` no halla raíz."""
    tokens = [t for t in re.split(r"\s+", (q or u"").strip()) if t]
    clauses = []
    for token in tokens:
        pattern = accent_insensitive_pattern(token)
        if not pattern:
            continue
        regex = {"$regex": pattern, "$options": "i"}
        clauses.append({"$or": [{"title": regex}, {"description": regex}, {"code": regex}]})
    if not clauses:
        return None
    return clauses[0] if len(clauses) == 1 else {"$and": clauses}


def title_match_regex(q):
    """Regex del primer token para priorizar coincidencias en título durante el fallback parcial."""
    tokens = [t for t in re.split(r"\s+", (q or u"").strip()) if t]
    if not tokens:
        return None
    pattern = accent_insensitive_pattern(tokens[0])
    return re.compile(pattern, re.IGNORECASE) if pattern else None


class CatalogService(object):

    def _types_and_areas(self):
        types = {t.id: t for t in VademecumSheetType.objects(isDeleted=False)}
        areas = {a.id: a for a in VademecumArea.objects(isDeleted=False)}
        return types, areas

    def _approved_comment_counts(self, sheetIds):
        """{sheetId: total de comentarios aprobados} en una sola consulta agregada."""
        ids = list({sid for sid in sheetIds if sid})
        if not ids:
            return {}
        rows = VademecumRating._get_collection().aggregate([
            {"$match": {"sheet": {"$in": ids}, "commentStatus": "approved"}},
            {"$group": {"_id": "$sheet", "count": {"$sum": 1}}},
        ])
        return {row["_id"]: row["count"] for row in rows}

    def summary(self, sheet, types, areas, commentCounts=None):
        sheetType = types.get(sheet.sheetType.id if hasattr(sheet.sheetType, "id")
                              else sheet.sheetType)
        sheetAreas = []
        for ref in sheet.areas:
            area = areas.get(ref.id if hasattr(ref, "id") else ref)
            if area:
                sheetAreas.append({"id": str(area.id), "name": area.name})
        return {
            "id": str(sheet.id),
            "code": sheet.code,
            "number": sheet.number,
            "title": sheet.title,
            "description": sheet.description,
            "sheetType": ({"id": str(sheetType.id), "name": sheetType.name,
                           "codePrefix": sheetType.codePrefix, "color": sheetType.color}
                          if sheetType else None),
            "grades": list(sheet.grades),
            "areas": sheetAreas,
            "thumbnailUrl": image_url(sheet, "thumbnail"),
            "previewUrl": image_url(sheet, "preview"),
            "publishedAt": isoformat(sheet.publishedAt),
            "ratingAverage": (round(float(sheet.ratingSum) / sheet.ratingCount, 1)
                              if sheet.ratingCount else None),
            "ratingCount": sheet.ratingCount,
            "commentCount": (commentCounts.get(sheet.id, 0) if commentCounts is not None else 0),
            "downloadCount": sheet.downloadCount or 0,
            "pageCount": sheet.file.pageCount if sheet.file else None,
        }

    def catalog_options(self):
        sheetTypes = []
        for t in VademecumSheetType.objects(isDeleted=False, status="1").order_by("sort"):
            sheetTypes.append({
                "id": str(t.id), "name": t.name, "codePrefix": t.codePrefix, "color": t.color,
                "sectionTitle": t.sectionTitle, "sectionText": t.sectionText, "sort": t.sort,
            })
        areas = [{"id": str(a.id), "name": a.name, "sort": a.sort,
                  "sheetTypeIds": [str(getattr(t, "id", t)) for t in a.sheetTypes]}
                 for a in VademecumArea.objects(isDeleted=False, status="1").order_by("sort")]
        grades = [{"value": g, "label": GRADE_LABELS[g]} for g in GRADES]
        return {"sheetTypes": sheetTypes, "areas": areas, "grades": grades}, 200

    def site_content(self):
        """Textos editables de las secciones del sitio, por clave (el HTML ya viene saneado)."""
        return {"records": [
            {"key": c.key, "title": c.title, "body": c.body, "updatedAt": isoformat(c.updatedAt)}
            for c in VademecumSiteContent.objects.order_by("key")]}, 200

    def teacher_grades(self, account):
        """Grados del docente en el año vigente, según su matrícula; [] si no hay sesión o matrícula."""
        if not account:
            return []
        from app.services.vademecum.enrollment_service import EnrollmentService
        return EnrollmentService().resolve(account.email).grades

    def _prioritized_page(self, sheets, order, grades, skip, limit):
        """(fichas de la página, total): primero las de `grades` y las de todos los grados.

        Es prioridad, no restricción: después de esas siguen las demás, cada grupo con el orden
        pedido. La página se arma sobre los dos grupos como si fueran una sola lista.
        """
        wanted = list(set(grades) | {"all"})
        first = sheets.filter(grades__in=wanted).order_by(*order)
        rest = sheets.filter(grades__nin=wanted).order_by(*order)
        nFirst = first.count()
        records = list(first.skip(skip).limit(limit)) if skip < nFirst else []
        missing = limit - len(records)
        if missing > 0:
            records += list(rest.skip(max(0, skip - nFirst)).limit(missing))
        return records, nFirst + rest.count()

    def home_indicators(self):
        """Indicadores públicos del Home: fichas, docentes activos, escuelas vinculadas y descargas."""
        from app.models.peca_project_model import PecaProject
        from app.models.vademecum import VademecumDownload, VademecumTeacherAccount
        from app.services.vademecum.enrollment_service import EnrollmentService

        sheets = VademecumSheet.objects(status="published", isDeleted=False).count()
        teachers = VademecumTeacherAccount.objects(status="1", isDeleted=False).count()
        # Solo hace falta el número: un $group en el año vigente evita traer nombres y después
        # descartar escuelas inactivas como hacía list_active_schools().
        schoolYear = EnrollmentService().current_school_year()
        schools = 0
        if schoolYear:
            rows = list(PecaProject._get_collection().aggregate([
                {"$match": {"schoolYear": {"$in": [schoolYear.id, str(schoolYear.id)]},
                            "isDeleted": False,
                            "project.school.id": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": "$project.school.id"}},
                {"$count": "count"},
            ]))
            schools = rows[0]["count"] if rows else 0
        downloads = VademecumDownload.objects(isRedownload=False).count()
        return {
            "sheets": sheets,
            "teachers": teachers,
            "schools": schools,
            "downloads": downloads,
        }

    def home_comments(self, types, limit=3):
        """Últimos comentarios aprobados y resumen global de valoraciones del catálogo."""
        from app.models.vademecum import VademecumTeacherAccount
        from app.services.vademecum.rating_service import author_name

        # Resumen global de valoraciones sobre fichas publicadas
        agg = list(VademecumSheet._get_collection().aggregate([
            {"$match": {"status": "published", "isDeleted": False, "ratingCount": {"$gt": 0}}},
            {"$group": {"_id": None,
                        "count": {"$sum": "$ratingCount"},
                        "sum": {"$sum": "$ratingSum"}}},
        ]))
        totalCount = agg[0]["count"] if agg else 0
        totalSum = agg[0]["sum"] if agg else 0
        ratingSummary = {
            "average": round(float(totalSum) / totalCount, 1) if totalCount else None,
            "count": totalCount,
        }

        publishedIds = [s.id for s in VademecumSheet.objects(
            status="published", isDeleted=False).only("id")]
        if not publishedIds:
            return [], ratingSummary
        # Se filtra por fichas publicadas antes de limitar: si no, los comentarios de fichas
        # despublicadas consumen el cupo y /home devuelve menos de `limit`.
        ratings = list(VademecumRating.objects(
            commentStatus="approved", comment__ne=None, sheet__in=publishedIds
        ).order_by("-updatedAt").limit(limit))
        if not ratings:
            return [], ratingSummary

        sheetIds = list({r.sheet.id if hasattr(r.sheet, "id") else r.sheet for r in ratings})
        accountIds = list({r.account.id if hasattr(r.account, "id") else r.account
                           for r in ratings})
        sheetsById = {
            s.id: s for s in VademecumSheet.objects(
                id__in=sheetIds, status="published", isDeleted=False
            ).only("id", "code", "title", "sheetType", "publishedAt", "fileReplacedAt",
                   "file.thumbnailPath", "file.previewPath")
        }
        accountsById = {
            a.id: a for a in VademecumTeacherAccount.objects(
                id__in=accountIds
            ).only("id", "firstName", "lastName")
        }

        comments = []
        for r in ratings:
            sid = r.sheet.id if hasattr(r.sheet, "id") else r.sheet
            sheet = sheetsById.get(sid)
            if not sheet:
                continue
            aid = r.account.id if hasattr(r.account, "id") else r.account
            account = accountsById.get(aid)
            stId = sheet.sheetType.id if hasattr(sheet.sheetType, "id") else sheet.sheetType
            sheetType = types.get(stId)
            comments.append({
                "id": str(r.id),
                "stars": r.stars,
                "comment": r.comment,
                "updatedAt": isoformat(r.updatedAt),
                "authorName": author_name(account) or u"Docente",
                "sheet": {
                    "id": str(sheet.id),
                    "code": sheet.code,
                    "title": sheet.title,
                    "sheetTypeName": sheetType.name if sheetType else None,
                    "color": sheetType.color if sheetType else None,
                    "thumbnailUrl": image_url(sheet, "thumbnail"),
                    "previewUrl": image_url(sheet, "preview"),
                },
            })
            if len(comments) >= limit:
                break
        return comments, ratingSummary

    def home(self, account=None):
        """Los 8 lanzamientos más recientes, las 8 fichas más descargadas, indicadores y comentarios.

        `downloadCount` solo suma la primera descarga por cuenta, ficha y año. Con matrícula,
        cada lista muestra primero las fichas de los grados del docente.
        """
        base = VademecumSheet.objects(status="published", isDeleted=False).only(*SUMMARY_FIELDS)
        grades = self.teacher_grades(account)

        def eight(sheets, order):
            if grades:
                return self._prioritized_page(sheets, order, grades, 0, HOME_SIZE)[0]
            return list(sheets.order_by(*order).limit(HOME_SIZE))

        types, areas = self._types_and_areas()
        comments, ratingSummary = self.home_comments(types)
        newReleases = eight(base, SORTS["newest"])
        featured = eight(base.filter(downloadCount__gt=0), SORTS["popular"])
        commentCounts = self._approved_comment_counts([s.id for s in newReleases + featured])
        return {
            "newReleases": [self.summary(s, types, areas, commentCounts) for s in newReleases],
            "featured": [self.summary(s, types, areas, commentCounts) for s in featured],
            "indicators": self.home_indicators(),
            "comments": comments,
            "ratingSummary": ratingSummary,
        }, 200

    def list_sheets(self, args, account=None):
        query = {"status": "published", "isDeleted": False}

        # `sheetTypeId` es repetible y convive con el singular que ya existía.
        typeIds = [object_id(value) for value in args.getlist("sheetTypeId") if value]
        if not all(typeIds):
            return invalid("sheetTypeId")
        if typeIds:
            if len(typeIds) == 1:
                query["sheetType"] = typeIds[0]
            else:
                query["sheetType__in"] = typeIds

        grades = [g for g in args.getlist("grade") if g]
        if grades:
            if any(g not in GRADES for g in grades):
                return invalid("grade")
            # Las fichas para todos los grados siempre aparecen
            wantedGrades = list(set(grades) | {"all"})
            query["grades__in"] = wantedGrades
        else:
            wantedGrades = []
        areaIds = [a for a in args.getlist("areaId") if a]
        areaObjectIds = []
        if areaIds:
            areaObjectIds = [object_id(a) for a in areaIds]
            if not all(areaObjectIds):
                return invalid("areaId")
            query["areas__in"] = areaObjectIds

        q = (args.get("q") or "").strip()
        if len(q) > MAX_QUERY_LENGTH:
            return {"q": [{"status": "13", "msg": "Invalid length"}]}, 400
        sort = args.get("sort") or "newest"
        if sort not in SORTS and sort not in AGG_SORTS and not (sort == "relevance" and q):
            return invalid("sort")
        onlyNew = truthy(args.get("onlyNew"))
        onlyPopular = truthy(args.get("onlyPopular"))
        onlyCommented = truthy(args.get("onlyCommented"))
        minRating = args.get("minRating")
        if minRating and minRating not in ("3", "4", "rated"):
            return invalid("minRating")
        try:
            page = int(args.get("page") or 1)
            pageSize = int(args.get("pageSize") or DEFAULT_PAGE_SIZE)
        except ValueError:
            return invalid("page")
        if page < 1 or not 1 <= pageSize <= MAX_PAGE_SIZE:
            return invalid("pageSize" if page >= 1 else "page")

        byCode = code_query(q) if q else None
        # CON-03: un docente con matrícula ve primero las fichas de sus grados, sin ocultar el
        # resto. Solo si no filtró por grado ni buscó texto (en ese caso manda su criterio).
        teacherGrades = [] if grades or q else self.teacher_grades(account)

        if sort in AGG_SORTS or onlyCommented or minRating:
            records, total = self._aggregated_page(
                query, typeIds, wantedGrades, areaObjectIds, byCode, q, sort, onlyNew,
                onlyPopular, onlyCommented, minRating, teacherGrades, page, pageSize)
            if total == 0 and q and not byCode:
                partial = partial_text_query(q)
                if partial:
                    records, total = self._aggregated_page(
                        query, typeIds, wantedGrades, areaObjectIds, partial, None, sort,
                        onlyNew, onlyPopular, onlyCommented, minRating, teacherGrades,
                        page, pageSize, isPartialFallback=True)
        else:
            baseSheets = VademecumSheet.objects(**query).only(*SUMMARY_FIELDS)
            if onlyNew:
                baseSheets = baseSheets.filter(
                    publishedAt__gte=datetime.utcnow() - timedelta(days=NEW_SHEET_WINDOW_DAYS))
            if onlyPopular:
                baseSheets = baseSheets.filter(downloadCount__gt=0)
            if teacherGrades:
                skip = (page - 1) * pageSize
                records, total = self._prioritized_page(
                    baseSheets, SORTS[sort], teacherGrades, skip, pageSize)
            else:
                sheets = baseSheets
                if byCode:
                    sheets = sheets.filter(__raw__=byCode)
                elif q:
                    sheets = sheets.search_text(q, language="spanish")
                if sort == "relevance" and byCode:
                    sheets = sheets.order_by("sheetType", "number")  # HT-2 antes que HT-10
                elif sort == "relevance":
                    sheets = sheets.order_by("$text_score")
                else:
                    sheets = sheets.order_by(*SORTS[sort])
                total = sheets.count()
                records = list(sheets.skip((page - 1) * pageSize).limit(pageSize))
                if total == 0 and q and not byCode:
                    partial = partial_text_query(q)
                    if partial:
                        fallback = baseSheets.filter(__raw__=partial)
                        total = fallback.count()
                        if total > 0:
                            if sort == "relevance":
                                titleRx = title_match_regex(q)
                                matched = list(fallback.order_by(*SORTS["newest"]))
                                if titleRx:
                                    matched.sort(key=lambda s: 0 if titleRx.search(s.title or u"")
                                                 else 1)
                                start = (page - 1) * pageSize
                                records = matched[start:start + pageSize]
                            else:
                                records = list(fallback.order_by(*SORTS[sort])
                                               .skip((page - 1) * pageSize).limit(pageSize))
        records = list(records)
        types, areas = self._types_and_areas()
        commentCounts = self._approved_comment_counts([s.id for s in records])
        return {
            "records": [self.summary(s, types, areas, commentCounts) for s in records],
            "pagination": {"page": page, "pageSize": pageSize, "total": total,
                           "pages": int(math.ceil(float(total) / pageSize))},
        }, 200

    def _aggregated_page(self, query, typeIds, grades, areaIds, byCode, q, sort, onlyNew,
                         onlyPopular, onlyCommented, minRating, teacherGrades, page, pageSize,
                         isPartialFallback=False):
        """Pipeline único para `sort=rating|commented` y los filtros calculados.

        `$text`, si hay búsqueda, va siempre primero. El total sale de un `$facet` sobre la
        propia colección de fichas, nunca de un recorte en memoria.
        """
        pipeline = []
        if byCode:
            pipeline.append({"$match": byCode})
        elif q:
            pipeline.append({"$match": {"$text": {"$search": q, "$language": "spanish"}}})

        match = {"status": query["status"], "isDeleted": query["isDeleted"]}
        if typeIds:
            match["sheetType"] = {"$in": typeIds}
        if grades:
            match["grades"] = {"$in": grades}
        if areaIds:
            match["areas"] = {"$in": areaIds}
        if onlyNew:
            match["publishedAt"] = {
                "$gte": datetime.utcnow() - timedelta(days=NEW_SHEET_WINDOW_DAYS)}
        if onlyPopular:
            match["downloadCount"] = {"$gt": 0}
        pipeline.append({"$match": match})

        addFields = {"ratingAverage": {"$cond": [
            {"$gt": ["$ratingCount", 0]},
            {"$divide": ["$ratingSum", "$ratingCount"]},
            None,
        ]}}
        if sort == "commented" or onlyCommented:
            pipeline.extend([
                {"$lookup": {
                    "from": "vademecum_ratings",
                    "let": {"sheetId": "$_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$sheet", "$$sheetId"]},
                                    "commentStatus": "approved"}},
                        {"$count": "count"},
                    ],
                    "as": "_approvedComments",
                }},
                {"$addFields": {"commentCount": {
                    "$ifNull": [{"$arrayElemAt": ["$_approvedComments.count", 0]}, 0]}}},
            ])
        pipeline.append({"$addFields": addFields})

        computedMatch = {}
        if onlyCommented:
            computedMatch["commentCount"] = {"$gt": 0}
        if minRating == "rated":
            computedMatch["ratingCount"] = {"$gt": 0}
        elif minRating in ("3", "4"):
            computedMatch["ratingAverage"] = {"$gte": int(minRating)}
        if computedMatch:
            pipeline.append({"$match": computedMatch})

        if teacherGrades:
            wanted = list(set(teacherGrades) | {"all"})
            pipeline.append({"$addFields": {"_priority": {"$cond": [
                {"$gt": [{"$size": {"$setIntersection": [
                    {"$ifNull": ["$grades", []]}, wanted]}}, 0]}, 0, 1]}}})

        order = []
        if teacherGrades:
            order.append(("_priority", 1))
        if sort == "rating":
            order += [("ratingAverage", -1), ("ratingCount", -1), ("publishedAt", -1)]
        elif sort == "commented":
            order += [("commentCount", -1), ("ratingAverage", -1), ("publishedAt", -1)]
        elif sort == "number" or (sort == "relevance" and byCode and not isPartialFallback):
            order += [("sheetType", 1), ("number", 1)]
        elif sort == "relevance" and not isPartialFallback:
            order += [("_text_score", {"$meta": "textScore"})]
        elif sort == "popular":
            order += [("downloadCount", -1), ("publishedAt", -1)]
        else:
            order += [("publishedAt", -1)]
        order.append(("_id", -1))
        pipeline.append({"$sort": dict(order)})

        projection = dict((field, 1) for field in SUMMARY_FIELDS)
        pipeline.append({"$facet": {
            "records": [{"$skip": (page - 1) * pageSize}, {"$limit": pageSize},
                        {"$project": projection}],
            "total": [{"$count": "count"}],
        }})

        result = list(VademecumSheet._get_collection().aggregate(pipeline))
        facet = result[0] if result else {"records": [], "total": []}
        records = [VademecumSheet._from_son(doc) for doc in facet["records"]]
        total = facet["total"][0]["count"] if facet["total"] else 0
        return records, total

    def published_sheet(self, sheetId, fields=None):
        """Ficha publicada; `fields` proyecta solo lo que necesita el llamador."""
        sheetId = object_id(sheetId)
        if not sheetId:
            return None
        sheets = VademecumSheet.objects(id=sheetId, status="published", isDeleted=False)
        if fields is not None:
            sheets = sheets.only(*fields)
        return sheets.first()

    def sheet_detail(self, sheetId):
        sheet = self.published_sheet(sheetId)
        if not sheet:
            return not_found()
        types, areas = self._types_and_areas()
        data = self.summary(sheet, types, areas)
        data.update({
            "description": sheet.description,
            "pageCount": sheet.file.pageCount if sheet.file else None,
            "sizeBytes": sheet.file.sizeBytes if sheet.file else None,
            "fileReplacedAt": isoformat(sheet.fileReplacedAt),
            "commentCount": VademecumRating.objects(sheet=sheet.id,
                                                    commentStatus="approved").count(),
        })
        return data, 200

    def image_path(self, sheetId, kind):
        """Ruta relativa de la imagen de una ficha publicada, o None."""
        sheet = self.published_sheet(
            sheetId, fields=("id", "file.thumbnailPath", "file.previewPath"))
        if not sheet or not sheet.file:
            return None
        return sheet.file.thumbnailPath if kind == "thumbnail" else sheet.file.previewPath

    def page_image_path(self, sheetId, pageNumber):
        """Ruta de la imagen nítida (1200 px) ya generada de una cara (1-based), o None."""
        if not isinstance(pageNumber, int) or pageNumber < 1:
            return None
        sheet = self.published_sheet(
            sheetId, fields=("id", "file.pageCount", "file.pdfPath"))
        if not sheet or not sheet.file or not sheet.file.pdfPath:
            return None
        if sheet.file.pageCount and pageNumber > sheet.file.pageCount:
            return None
        relative = os.path.join(os.path.dirname(sheet.file.pdfPath),
                                "page-{}.webp".format(pageNumber))
        from app.services.vademecum.sheet_media import storage_root

        root = storage_root()
        if not root:
            return None
        target = os.path.realpath(os.path.join(root, relative))
        if not target.startswith(root + os.sep) or not os.path.isfile(target):
            return None
        return target
