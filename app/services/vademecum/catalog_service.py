# -*- coding: utf-8 -*-
# app/services/vademecum/catalog_service.py
"""Catálogo público de fichas (API-13, GES-03).

Solo fichas `published` y sin borrar. Nunca expone la ruta ni el enlace del PDF: la descarga
es un POST con sesión (API-14). Las imágenes que se publican son la miniatura y la vista
previa de baja resolución que genera API-10.
"""

import calendar
import math

from bson import ObjectId
from bson.errors import InvalidId

from app.models.vademecum import (
    VademecumArea, VademecumRating, VademecumSheet, VademecumSheetType)
from app.models.vademecum.constants import GRADE_LABELS, GRADES

SORTS = {
    "newest": ("-publishedAt", "-id"),
    "number": ("sheetType", "seriesId", "number"),
    "popular": ("-downloadCount", "-publishedAt"),
}
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MAX_QUERY_LENGTH = 100
# Campos que el listado necesita: deja fuera searchText, sourcePages y rutas de archivos
SUMMARY_FIELDS = ("id", "code", "number", "title", "sheetType", "seriesId", "grades", "areas",
                  "publishedAt", "fileReplacedAt", "ratingCount", "ratingSum",
                  "file.thumbnailPath", "file.previewPath")


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


def series_dict(series, full=False):
    data = {"id": str(series.id), "name": series.name, "code": series.code}
    if full:
        data.update(grades=list(series.grades), sort=series.sort)
    return data


def image_url(sheet, kind):
    """URL pública de la imagen con ?v= para invalidar caché, o None si no existe."""
    path = sheet.file and (sheet.file.thumbnailPath if kind == "thumbnail"
                           else sheet.file.previewPath)
    if not path:
        return None
    version = sheet.fileReplacedAt or sheet.publishedAt
    suffix = "?v={}".format(calendar.timegm(version.utctimetuple())) if version else ""
    return "/vademecum/sheets/{}/{}.webp{}".format(sheet.id, kind, suffix)


class CatalogService(object):

    def _types_and_areas(self):
        types = {t.id: t for t in VademecumSheetType.objects(isDeleted=False)}
        areas = {a.id: a for a in VademecumArea.objects(isDeleted=False)}
        return types, areas

    def summary(self, sheet, types, areas):
        sheetType = types.get(sheet.sheetType.id if hasattr(sheet.sheetType, "id")
                              else sheet.sheetType)
        series = sheetType.get_series(sheet.seriesId) if sheetType else None
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
            "series": series_dict(series) if series else None,
            "grades": list(sheet.grades),
            "areas": sheetAreas,
            "thumbnailUrl": image_url(sheet, "thumbnail"),
            "previewUrl": image_url(sheet, "preview"),
            "publishedAt": isoformat(sheet.publishedAt),
            "ratingAverage": (round(float(sheet.ratingSum) / sheet.ratingCount, 1)
                              if sheet.ratingCount else None),
            "ratingCount": sheet.ratingCount,
        }

    def catalog_options(self):
        sheetTypes = []
        for t in VademecumSheetType.objects(isDeleted=False, status="1").order_by("sort"):
            sheetTypes.append({
                "id": str(t.id), "name": t.name, "codePrefix": t.codePrefix, "color": t.color,
                "sectionTitle": t.sectionTitle, "sectionText": t.sectionText, "sort": t.sort,
                "series": [series_dict(s, full=True)
                           for s in sorted(t.active_series(), key=lambda s: s.sort)],
            })
        areas = [{"id": str(a.id), "name": a.name, "sort": a.sort}
                 for a in VademecumArea.objects(isDeleted=False, status="1").order_by("sort")]
        grades = [{"value": g, "label": GRADE_LABELS[g]} for g in GRADES]
        return {"sheetTypes": sheetTypes, "areas": areas, "grades": grades}, 200

    def list_sheets(self, args):
        query = {"status": "published", "isDeleted": False}

        sheetTypeId = args.get("sheetTypeId")
        if sheetTypeId:
            query["sheetType"] = object_id(sheetTypeId)
            if not query["sheetType"]:
                return invalid("sheetTypeId")
        seriesId = args.get("seriesId")
        if seriesId:
            query["seriesId"] = object_id(seriesId)
            if not query["seriesId"]:
                return invalid("seriesId")
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
        if q:
            sheets = sheets.search_text(q, language="spanish")
        if sort == "relevance":
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
