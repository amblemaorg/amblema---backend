# -*- coding: utf-8 -*-
# app/services/vademecum/library_service.py
"""Biblioteca personal del docente: favoritos y mis descargas (API-15, GES-03 5.3).

Reglas:
- Cada docente ve solo lo suyo: todas las consultas parten de su cuenta.
- Favoritos: poner o quitar es idempotente. Una ficha despublicada o borrada no aparece en el
  listado, pero su favorito se conserva por si se vuelve a publicar.
- Mis descargas: una fila por ficha y año (la última descarga). `timesDownloaded` cuenta la
  descarga y sus redescargas. Sin `schoolYearId`, el año vigente.
"""

from datetime import datetime

from bson import ObjectId
from mongoengine.errors import NotUniqueError

from app.models.vademecum import VademecumDownload, VademecumFavorite, VademecumSheet
from app.services.vademecum.catalog_service import (
    SUMMARY_FIELDS, CatalogService, invalid, isoformat, not_found, object_id)
from app.services.vademecum.enrollment_service import EnrollmentService
from app.services.vademecum.rating_service import _page_args, _pagination


class LibraryService(object):

    def __init__(self, enrollmentService=None):
        self.enrollment = enrollmentService or EnrollmentService()
        self.catalog = CatalogService()

    def _published_by_id(self, ids):
        """{ObjectId: ficha} de las publicadas entre `ids`, solo con los campos del resumen."""
        sheets = VademecumSheet.objects(
            id__in=ids, status="published", isDeleted=False).only(*SUMMARY_FIELDS)
        return {sheet.id: sheet for sheet in sheets}

    # --- Favoritos ---

    def list_favorites(self, account, args):
        page, pageSize, failure = _page_args(args)
        if failure:
            return failure
        # Los favoritos de un docente son pocos: se filtran las fichas ya no publicadas antes
        # de paginar para que `total` coincida con lo que se ve.
        rows = list(VademecumFavorite._get_collection().find(
            {"account": account.id}, {"sheet": 1, "createdAt": 1}).sort("createdAt", -1))
        sheets = self._published_by_id([row["sheet"] for row in rows])
        visible = [row for row in rows if row["sheet"] in sheets]
        pageRows = visible[(page - 1) * pageSize:page * pageSize]
        types, areas = self.catalog._types_and_areas()
        return {
            "records": [{"sheet": self.catalog.summary(sheets[row["sheet"]], types, areas),
                         "createdAt": isoformat(row["createdAt"])} for row in pageRows],
            "pagination": _pagination(page, pageSize, len(visible)),
        }, 200

    def add_favorite(self, account, sheetId):
        sheet = self.catalog.published_sheet(sheetId)
        if not sheet:
            return not_found()
        now = datetime.utcnow()
        try:
            VademecumFavorite.objects(account=account.id, sheet=sheet.id).update_one(
                upsert=True, set_on_insert__createdAt=now, set__updatedAt=now)
        except NotUniqueError:
            pass  # otra petición idéntica lo guardó antes: el resultado es el mismo
        return "", 204

    def remove_favorite(self, account, sheetId):
        objectId = object_id(sheetId)
        if not objectId:
            return not_found()
        VademecumFavorite.objects(account=account.id, sheet=objectId).delete()
        return "", 204

    # --- Mis descargas ---

    def list_downloads(self, account, args):
        page, pageSize, failure = _page_args(args)
        if failure:
            return failure
        collection = VademecumDownload._get_collection()
        accountId = str(account.id)

        years = [{"id": row["_id"], "name": row.get("name")} for row in collection.aggregate([
            {"$match": {"account.id": accountId}},
            {"$group": {"_id": "$schoolYear.id", "name": {"$first": "$schoolYear.name"},
                        "last": {"$max": "$createdAt"}}},
            {"$sort": {"last": -1}},
        ])]

        yearId = args.get("schoolYearId")
        if yearId:
            if not object_id(yearId):
                return invalid("schoolYearId")
        else:
            current = self.enrollment.current_school_year()
            yearId = str(current.id) if current else None

        rows = []
        if yearId:
            rows = list(collection.aggregate([
                {"$match": {"account.id": accountId, "schoolYear.id": yearId}},
                {"$sort": {"createdAt": -1}},
                {"$group": {"_id": "$sheet.id", "schoolYear": {"$first": "$schoolYear"},
                            "school": {"$first": "$school"}, "origin": {"$first": "$origin"},
                            "lastDownloadedAt": {"$first": "$createdAt"},
                            "timesDownloaded": {"$sum": 1}}},
                {"$sort": {"lastDownloadedAt": -1}},
            ]))
        sheets = self._published_by_id([ObjectId(row["_id"]) for row in rows])
        visible = [row for row in rows if ObjectId(row["_id"]) in sheets]
        pageRows = visible[(page - 1) * pageSize:page * pageSize]
        types, areas = self.catalog._types_and_areas()
        records = []
        for row in pageRows:
            school = row.get("school")
            records.append({
                "sheet": self.catalog.summary(sheets[ObjectId(row["_id"])], types, areas),
                "schoolYear": {"id": row["schoolYear"]["id"], "name": row["schoolYear"].get("name")},
                # MongoEngine omite los campos nulos: el nombre o el código pueden faltar
                "school": ({"id": school["id"], "name": school.get("name"),
                            "code": school.get("code")} if school else None),
                "origin": row["origin"],
                "lastDownloadedAt": isoformat(row["lastDownloadedAt"]),
                "timesDownloaded": row["timesDownloaded"],
            })
        return {"years": years, "records": records,
                "pagination": _pagination(page, pageSize, len(visible))}, 200
