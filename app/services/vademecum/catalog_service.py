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
HOME_SIZE = 8
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MAX_QUERY_LENGTH = 100
# Campos que el listado necesita: deja fuera searchText, sourcePages y rutas de archivos
SUMMARY_FIELDS = ("id", "code", "number", "title", "sheetType", "grades", "areas",
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


class CatalogService(object):

    def _types_and_areas(self):
        types = {t.id: t for t in VademecumSheetType.objects(isDeleted=False)}
        areas = {a.id: a for a in VademecumArea.objects(isDeleted=False)}
        return types, areas

    def summary(self, sheet, types, areas):
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

    def home(self, account=None):
        """Los 8 lanzamientos más recientes y las 8 fichas más descargadas (sin redescargas).

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
        return {
            "newReleases": [self.summary(s, types, areas) for s in eight(base, SORTS["newest"])],
            "featured": [self.summary(s, types, areas)
                         for s in eight(base.filter(downloadCount__gt=0), SORTS["popular"])],
        }, 200

    def list_sheets(self, args, account=None):
        query = {"status": "published", "isDeleted": False}

        sheetTypeId = args.get("sheetTypeId")
        if sheetTypeId:
            query["sheetType"] = object_id(sheetTypeId)
            if not query["sheetType"]:
                return invalid("sheetTypeId")
        grades = [g for g in args.getlist("grade") if g]
        if grades:
            if any(g not in GRADES for g in grades):
                return invalid("grade")
            # Las fichas para todos los grados siempre aparecen
            query["grades__in"] = list(set(grades) | {"all"})
        areaIds = [a for a in args.getlist("areaId") if a]
        if areaIds:
            ids = [object_id(a) for a in areaIds]
            if not all(ids):
                return invalid("areaId")
            query["areas__in"] = ids

        q = (args.get("q") or "").strip()
        if len(q) > MAX_QUERY_LENGTH:
            return {"q": [{"status": "13", "msg": "Invalid length"}]}, 400
        sort = args.get("sort") or "newest"
        if sort not in SORTS and not (sort == "relevance" and q):
            return invalid("sort")
        try:
            page = int(args.get("page") or 1)
            pageSize = int(args.get("pageSize") or DEFAULT_PAGE_SIZE)
        except ValueError:
            return invalid("page")
        if page < 1 or not 1 <= pageSize <= MAX_PAGE_SIZE:
            return invalid("pageSize" if page >= 1 else "page")

        sheets = VademecumSheet.objects(**query).only(*SUMMARY_FIELDS)
        # CON-03: un docente con matrícula ve primero las fichas de sus grados, sin ocultar el
        # resto. Solo si no filtró por grado ni buscó texto (en ese caso manda su criterio).
        teacherGrades = [] if grades or q else self.teacher_grades(account)
        if teacherGrades:
            skip = (page - 1) * pageSize
            records, total = self._prioritized_page(
                sheets, SORTS[sort], teacherGrades, skip, pageSize)
        else:
            byCode = code_query(q) if q else None
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
            records = sheets.skip((page - 1) * pageSize).limit(pageSize)
        types, areas = self._types_and_areas()
        return {
            "records": [self.summary(s, types, areas) for s in records],
            "pagination": {"page": page, "pageSize": pageSize, "total": total,
                           "pages": int(math.ceil(float(total) / pageSize))},
        }, 200

    def published_sheet(self, sheetId):
        sheetId = object_id(sheetId)
        if not sheetId:
            return None
        return VademecumSheet.objects(id=sheetId, status="published", isDeleted=False).first()

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
        sheet = self.published_sheet(sheetId)
        if not sheet or not sheet.file:
            return None
        return sheet.file.thumbnailPath if kind == "thumbnail" else sheet.file.previewPath

    def page_image_path(self, sheetId, pageNumber):
        """Ruta absoluta de la imagen WebP nítida de una cara (1-based) del PDF, o None."""
        if not isinstance(pageNumber, int) or pageNumber < 1:
            return None
        sheet = self.published_sheet(sheetId)
        if not sheet or not sheet.file:
            return None
        if sheet.file.pageCount and pageNumber > sheet.file.pageCount:
            return None
        from app.services.vademecum.download_service import pdf_path
        from app.services.vademecum.sheet_media import render_pdf_page

        pdf = pdf_path(sheet)
        if not pdf:
            return None
        target = os.path.join(os.path.dirname(pdf), "page-{}.webp".format(pageNumber))
        if not os.path.isfile(target) or os.path.getmtime(target) < os.path.getmtime(pdf):
            if not render_pdf_page(pdf, pageNumber, target):
                return None
        return target
