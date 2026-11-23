# -*- coding: utf-8 -*-
# app/services/vademecum/indicator_service.py
"""Indicadores de uso para el backoffice (API-17, GES-03 "Admin · Indicadores").

Todo sale de `vademecum_downloads`, que guarda una foto de la ficha, la cuenta, la escuela y
la región en cada descarga: no hace falta cruzar con PECA ni con las escuelas.

Reglas:
- Los indicadores no cuentan redescargas (`isRedownload=False`); el detalle de un docente sí
  las lista, marcadas.
- Los externos no tienen escuela: en el ranking de escuelas forman una sola fila "Externos"
  (`school.id = null`). Filtrar por escuela o región los deja fuera.
- Excel y PDF los arma el backoffice; la API entrega JSON.
"""

import math
import re
from datetime import datetime

from app.models.school_year_model import SchoolYear
from app.models.vademecum import VademecumDownload, VademecumSheetType, VademecumTeacherAccount
from app.models.vademecum.constants import ORIGINS
from app.services.vademecum.catalog_service import (
    DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MAX_QUERY_LENGTH, invalid, isoformat, not_found, object_id)
from app.services.vademecum.enrollment_service import EnrollmentService

DEFAULT_TOP = 10
MAX_TOP = 50
EXTERNAL_SCHOOL_NAME = "Externos"
# Tope de filas de la exportación: más allá se pide al usuario acotar los filtros
MAX_EXPORT_ROWS = 5000
ORIGIN_LABELS = {"enrollment": u"Matrícula", "external": u"Externo"}


def _year_ref(schoolYear):
    return {"id": str(schoolYear.id), "name": schoolYear.name} if schoolYear else None


def _school_ref(school):
    if not school:
        return None
    return {"id": school.get("id"), "name": school.get("name"), "code": school.get("code"),
            "stateName": school.get("stateName")}


def _account_ref(account):
    return {"id": account.get("id"), "email": account.get("email"),
            "firstName": account.get("firstName"), "lastName": account.get("lastName")}


def _empty_page(pageSize=DEFAULT_PAGE_SIZE):
    return {"records": [], "pagination": {"page": 1, "pageSize": pageSize, "total": 0,
                                          "pages": 0}}


def _page_args(args):
    try:
        page = int(args.get("page") or 1)
        pageSize = int(args.get("pageSize") or DEFAULT_PAGE_SIZE)
    except (TypeError, ValueError):
        return None, None, invalid("page")
    if page < 1:
        return None, None, invalid("page")
    if not 1 <= pageSize <= MAX_PAGE_SIZE:
        return None, None, invalid("pageSize")
    return page, pageSize, None


def _pagination(page, pageSize, total):
    return {"page": page, "pageSize": pageSize, "total": total,
            "pages": int(math.ceil(float(total) / pageSize))}


def _count(facet):
    return facet[0]["n"] if facet else 0


class IndicatorService(object):

    def __init__(self, enrollmentService=None):
        self.enrollment = enrollmentService or EnrollmentService()

    # --- Filtros comunes ---

    def _school_year(self, args):
        """(año, error). Sin `schoolYearId` usa el vigente; puede no haber ninguno."""
        schoolYearId = args.get("schoolYearId")
        if not schoolYearId:
            return self.enrollment.current_school_year(), None
        schoolYearOid = object_id(schoolYearId)
        schoolYear = schoolYearOid and SchoolYear.objects(id=schoolYearOid).first()
        return (schoolYear, None) if schoolYear else (None, invalid("schoolYearId"))

    def _match(self, schoolYear, args, fields):
        """Filtro de las descargas que cuentan. `fields` dice qué filtros acepta la ruta."""
        match = {"schoolYear.id": str(schoolYear.id), "isRedownload": False}
        for name, path in (("schoolId", "school.id"), ("stateId", "school.stateId"),
                           ("sheetTypeId", "sheet.sheetTypeId")):
            value = args.get(name) if name in fields else None
            if value:
                if not object_id(value):
                    return None, invalid(name)
                match[path] = value
        origin = args.get("origin") if "origin" in fields else None
        if origin:
            if origin not in ORIGINS:
                return None, invalid("origin")
            match["origin"] = origin
        return match, None

    # --- GET /vademecum/admin/indicators ---

    def summary(self, args):
        schoolYear, failure = self._school_year(args)
        if failure:
            return failure
        try:
            top = int(args.get("top") or DEFAULT_TOP)
        except (TypeError, ValueError):
            return invalid("top")
        if not 1 <= top <= MAX_TOP:
            return invalid("top")
        if not schoolYear:
            return self._empty_summary(None), 200
        match, failure = self._match(
            schoolYear, args, ("schoolId", "stateId", "sheetTypeId", "origin"))
        if failure:
            return failure

        # Una sola consulta. El orden por fecha descendente hace que $first tome la foto
        # más reciente de nombres y códigos.
        pipeline = [
            {"$match": match},
            {"$sort": {"createdAt": -1}},
            {"$facet": {
                "downloads": [{"$count": "n"}],
                "teachers": [{"$group": {"_id": "$account.id"}}, {"$count": "n"}],
                "externalTeachers": [{"$match": {"origin": "external"}},
                                     {"$group": {"_id": "$account.id"}}, {"$count": "n"}],
                "schools": [{"$match": {"school.id": {"$ne": None}}},
                            {"$group": {"_id": "$school.id"}}, {"$count": "n"}],
                "byType": [{"$group": {"_id": "$sheet.sheetTypeId",
                                       "name": {"$first": "$sheet.sheetTypeName"},
                                       "downloads": {"$sum": 1}}},
                           {"$sort": {"downloads": -1, "_id": 1}}],
                "byOrigin": [{"$group": {"_id": "$origin", "downloads": {"$sum": 1}}}],
                "topSheets": [{"$group": {"_id": "$sheet.id", "code": {"$first": "$sheet.code"},
                                          "title": {"$first": "$sheet.title"},
                                          "downloads": {"$sum": 1}}},
                              {"$sort": {"downloads": -1, "code": 1}}, {"$limit": top}],
                "topTeachers": [{"$group": {"_id": "$account.id",
                                            "account": {"$first": "$account"},
                                            "downloads": {"$sum": 1}}},
                                {"$sort": {"downloads": -1, "_id": 1}}, {"$limit": top}],
                # school.id null agrupa a todos los externos en una fila
                "topSchools": [{"$group": {"_id": {"$ifNull": ["$school.id", None]},
                                           "school": {"$first": "$school"},
                                           "teachers": {"$addToSet": "$account.id"},
                                           "downloads": {"$sum": 1}}},
                               {"$sort": {"downloads": -1, "_id": 1}}, {"$limit": top}],
            }},
        ]
        result = list(VademecumDownload.objects.aggregate(pipeline))[0]

        data = self._empty_summary(schoolYear)
        data["totals"] = {"downloads": _count(result["downloads"]),
                          "activeTeachers": _count(result["teachers"]),
                          "activeSchools": _count(result["schools"]),
                          "externalTeachers": _count(result["externalTeachers"])}
        data["byType"] = self._by_type(result["byType"])
        for row in result["byOrigin"]:
            data["byOrigin"][row["_id"]] = row["downloads"]
        data["topSheets"] = [{"sheet": {"id": row["_id"], "code": row.get("code"),
                                        "title": row.get("title")},
                              "downloads": row["downloads"]} for row in result["topSheets"]]
        data["topTeachers"] = [{"account": _account_ref(row["account"]),
                                "downloads": row["downloads"]}
                               for row in result["topTeachers"]]
        data["topSchools"] = [{"school": self._ranking_school(row),
                               "downloads": row["downloads"],
                               "activeTeachers": len(row["teachers"])}
                              for row in result["topSchools"]]
        return data, 200

    def _empty_summary(self, schoolYear):
        return {"schoolYear": _year_ref(schoolYear),
                "totals": {"downloads": 0, "activeTeachers": 0, "activeSchools": 0,
                           "externalTeachers": 0},
                "byType": [], "byOrigin": {origin: 0 for origin in ORIGINS},
                "topSheets": [], "topTeachers": [], "topSchools": []}

    def _by_type(self, rows):
        """Nombre, prefijo y color actuales del tipo; si se borró, el nombre de la foto."""
        ids = [object_id(row["_id"]) for row in rows if object_id(row["_id"])]
        types = {str(t.id): t for t in VademecumSheetType.objects(id__in=ids)}
        result = []
        for row in rows:
            sheetType = types.get(row["_id"])
            result.append({
                "sheetType": {"id": row["_id"],
                              "name": sheetType.name if sheetType else row.get("name"),
                              "codePrefix": sheetType.codePrefix if sheetType else None,
                              "color": sheetType.color if sheetType else None},
                "downloads": row["downloads"]})
        return result

    @staticmethod
    def _ranking_school(row):
        if row["_id"] is None:
            return {"id": None, "name": EXTERNAL_SCHOOL_NAME, "code": None, "stateName": None}
        return _school_ref(row["school"])

    # --- GET /vademecum/admin/indicators/teachers ---

    def teachers(self, args):
        schoolYear, failure = self._school_year(args)
        if failure:
            return failure
        page, pageSize, failure = _page_args(args)
        if failure:
            return failure
        if not schoolYear:
            return _empty_page(pageSize), 200
        pipeline, failure = self._teachers_pipeline(schoolYear, args)
        if failure:
            return failure
        pipeline.append({"$facet": {
            "total": [{"$count": "n"}],
            "records": [{"$sort": {"downloads": -1, "account.email": 1}},
                        {"$skip": (page - 1) * pageSize}, {"$limit": pageSize}]}})
        result = list(VademecumDownload.objects.aggregate(pipeline))[0]

        records = []
        for row in result["records"]:
            # Una escuela por id aunque su nombre haya cambiado entre descargas
            unique = {s["id"]: _school_ref(s) for s in row["schools"] if s}
            schools = sorted(unique.values(), key=lambda s: s["name"] or "")
            records.append({"account": _account_ref(row["account"]), "schools": schools,
                            "origin": row["origin"], "downloads": row["downloads"],
                            "lastDownloadAt": isoformat(row["lastDownloadAt"])})
        return {"records": records,
                "pagination": _pagination(page, pageSize, _count(result["total"]))}, 200

    def _teachers_pipeline(self, schoolYear, args):
        """(pipeline, error): una fila por docente, con filtros y búsqueda `q` ya aplicados.
        Lo comparten el listado y la exportación."""
        match, failure = self._match(
            schoolYear, args, ("schoolId", "stateId", "sheetTypeId", "origin"))
        if failure:
            return None, failure
        q = (args.get("q") or "").strip()
        if len(q) > MAX_QUERY_LENGTH:
            return None, invalid("q")

        pipeline = [{"$match": match}, {"$sort": {"createdAt": -1}},
                    {"$group": {"_id": "$account.id", "account": {"$first": "$account"},
                                "origin": {"$first": "$origin"},
                                "schools": {"$addToSet": "$school"},
                                "downloads": {"$sum": 1},
                                "lastDownloadAt": {"$max": "$createdAt"}}}]
        if q:
            pattern = {"$regex": re.escape(q), "$options": "i"}
            pipeline.append({"$match": {"$or": [{"account.email": pattern},
                                                {"account.firstName": pattern},
                                                {"account.lastName": pattern}]}})
        return pipeline, None

    # --- GET /vademecum/admin/indicators/teachers/export ---

    def export_teachers(self, args):
        schoolYear, failure = self._school_year(args)
        if failure:
            return failure
        filters = {name: args.get(name) or None
                   for name in ("schoolId", "stateId", "sheetTypeId", "origin", "q")}
        data = {"schoolYear": _year_ref(schoolYear), "generatedAt": isoformat(datetime.utcnow()),
                "filters": filters, "total": 0, "records": []}
        if not schoolYear:
            return data, 200
        pipeline, failure = self._teachers_pipeline(schoolYear, args)
        if failure:
            return failure
        # Se pide una fila de más solo para saber si se pasó del tope
        pipeline.append({"$limit": MAX_EXPORT_ROWS + 1})
        rows = list(VademecumDownload.objects.aggregate(pipeline))
        if len(rows) > MAX_EXPORT_ROWS:
            return invalid("general", "Too many rows, narrow the filters")

        records = [self._export_record(row) for row in rows]
        records.sort(key=lambda r: (-r["downloads"], (r["lastName"] or u"").lower(),
                                    (r["firstName"] or u"").lower()))
        data["total"] = len(records)
        data["records"] = records
        return data, 200

    @staticmethod
    def _export_record(row):
        """Fila plana (solo texto y números) lista para xlsx y pdfmake."""
        account = row["account"]
        # Una escuela por id aunque su nombre haya cambiado entre descargas
        schools = {s["id"]: s for s in row["schools"] if s}.values()

        def joined(key):
            return u", ".join(sorted({s.get(key) for s in schools if s.get(key)}))

        return {"firstName": account.get("firstName"), "lastName": account.get("lastName"),
                "email": account.get("email"), "origin": row["origin"],
                "originLabel": ORIGIN_LABELS.get(row["origin"], row["origin"]),
                "schools": joined("name"), "schoolCodes": joined("code"),
                "states": joined("stateName"), "downloads": row["downloads"],
                "lastDownloadAt": isoformat(row["lastDownloadAt"])}

    # --- GET /vademecum/admin/indicators/teachers/{accountId}/downloads ---

    def teacher_downloads(self, accountId, args):
        accountOid = object_id(accountId)
        if not accountOid or not VademecumTeacherAccount.objects(id=accountOid).first():
            return not_found()
        schoolYear, failure = self._school_year(args)
        if failure:
            return failure
        page, pageSize, failure = _page_args(args)
        if failure:
            return failure
        if not schoolYear:
            return _empty_page(pageSize), 200
        # El detalle sí incluye redescargas, marcadas con isRedownload
        downloads = VademecumDownload.objects(
            __raw__={"account.id": str(accountOid), "schoolYear.id": str(schoolYear.id)}
        ).order_by("-createdAt")
        total = downloads.count()
        records = downloads.skip((page - 1) * pageSize).limit(pageSize)
        return {"records": [download_record(d) for d in records],
                "pagination": _pagination(page, pageSize, total)}, 200


def download_record(download):
    sheet, school, year = download.sheet, download.school, download.schoolYear
    return {
        "id": str(download.id),
        "sheet": {"id": sheet.id, "code": sheet.code, "title": sheet.title,
                  "sheetTypeName": sheet.sheetTypeName},
        "school": ({"id": school.id, "name": school.name, "code": school.code,
                    "stateName": school.stateName} if school else None),
        "schoolYear": {"id": year.id, "name": year.name},
        "origin": download.origin,
        "isRedownload": download.isRedownload,
        "createdAt": isoformat(download.createdAt),
    }
