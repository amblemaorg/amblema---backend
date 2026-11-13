# -*- coding: utf-8 -*-
# app/services/vademecum/taxonomy_admin_service.py
"""Administración de tipos de ficha (con series) y áreas (API-12, GES-03)."""

from bson import ObjectId
from marshmallow import ValidationError
from mongoengine.errors import NotUniqueError
from mongoengine.errors import ValidationError as ModelValidationError

from app.models.vademecum import SheetSeries, VademecumArea, VademecumSheet, VademecumSheetType
from app.schemas.vademecum.admin_schema import AreaInputSchema, SheetTypeInputSchema
from app.services.vademecum.catalog_service import object_id, series_dict

DUPLICATED = [{"status": "1", "msg": "Duplicated record found"}]
IN_USE = ({"general": [{"status": "119", "msg": "Record has associated sheets"}]}, 409)


def _sheet_counts(field):
    """{id: fichas sin borrar} agrupando por `field` (sheetType o areas)."""
    pipeline = [{"$match": {"isDeleted": False}}]
    if field == "areas":
        pipeline.append({"$unwind": "$areas"})
    pipeline.append({"$group": {"_id": "$" + field, "count": {"$sum": 1}}})
    return {row["_id"]: row["count"]
            for row in VademecumSheet._get_collection().aggregate(pipeline)}


def _model_errors(exc):
    """ValidationError de MongoEngine al formato de la API."""
    errors = getattr(exc, "errors", None) or {}
    # Lo que lanza clean() llega envuelto en "__all__" con los campos dentro
    inner = getattr(errors.get("__all__"), "errors", None)
    if inner:
        errors = inner
    if errors:
        return {field: [{"status": "1", "msg": str(msg)}] for field, msg in errors.items()}, 400
    return {"general": [{"status": "1", "msg": str(exc)}]}, 400


# --- Tipos de ficha ---

def sheet_type_dict(sheetType, sheetCount=0):
    return {
        "id": str(sheetType.id), "name": sheetType.name, "headerName": sheetType.headerName,
        "codePrefix": sheetType.codePrefix, "color": sheetType.color,
        "sectionTitle": sheetType.sectionTitle, "sectionText": sheetType.sectionText,
        "sort": sheetType.sort, "status": sheetType.status, "sheetCount": sheetCount,
        "series": [series_dict(s, full=True)
                   for s in sorted(sheetType.active_series(), key=lambda s: s.sort)],
    }


class SheetTypeAdminService(object):

    def get(self, sheetTypeId):
        sheetTypeId = object_id(sheetTypeId)
        return sheetTypeId and VademecumSheetType.objects(id=sheetTypeId,
                                                          isDeleted=False).first()

    def list(self):
        counts = _sheet_counts("sheetType")
        types = VademecumSheetType.objects(isDeleted=False).order_by("sort", "name")
        return {"records": [sheet_type_dict(t, counts.get(t.id, 0)) for t in types]}, 200

    def create(self, jsonData):
        try:
            data = SheetTypeInputSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        sheetType = VademecumSheetType()
        failure = self._apply(sheetType, data)
        if failure:
            return failure
        return self._save(sheetType, created=True)

    def update(self, sheetType, jsonData):
        try:
            data = SheetTypeInputSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        before = self._codes(sheetType)
        failure = self._apply(sheetType, data)
        if failure:
            return failure
        response = self._save(sheetType)
        if response[1] == 200 and self._codes(sheetType) != before:
            # El código de la ficha sale del prefijo y la serie: se recalcula (clean)
            for sheet in VademecumSheet.objects(sheetType=sheetType.id, isDeleted=False):
                sheet.save()
        return response

    def delete(self, sheetType):
        if VademecumSheet.objects(sheetType=sheetType.id, isDeleted=False).first():
            return IN_USE
        sheetType.isDeleted = True
        sheetType.save()
        return "", 204

    def _codes(self, sheetType):
        return (sheetType.codePrefix,
                tuple(sorted((str(s.id), s.code) for s in sheetType.series)))

    def _apply(self, sheetType, data):
        for field in ("name", "headerName", "codePrefix", "color", "sectionTitle",
                      "sectionText", "sort", "status"):
            setattr(sheetType, field, data[field])
        sheetType.codePrefix = data["codePrefix"].upper()

        existing = {str(s.id): s for s in sheetType.series}
        kept = set()
        series = []
        for item in data["series"]:
            if item.get("id"):
                current = existing.get(item["id"])
                if not current:
                    return {"series": [{"status": "1", "msg": "Series not found"}]}, 400
                kept.add(item["id"])
            else:
                current = SheetSeries(id=ObjectId())
            current.name, current.code = item["name"], item["code"]
            current.grades, current.sort = item["grades"], item["sort"]
            current.isDeleted = False
            series.append(current)
        # Las series que no vienen se borran; si tienen fichas, solo se ocultan
        used = set()
        if sheetType.id:
            used = set(str(v) for v in VademecumSheet.objects(
                sheetType=sheetType.id, isDeleted=False).distinct("seriesId") if v)
        for seriesId, current in existing.items():
            if seriesId not in kept and seriesId in used:
                current.isDeleted = True
                series.append(current)
        sheetType.series = series
        return None

    def _save(self, sheetType, created=False):
        try:
            sheetType.save()
        except NotUniqueError:
            return {"codePrefix": DUPLICATED}, 400
        except ModelValidationError as exc:
            return _model_errors(exc)
        count = VademecumSheet.objects(sheetType=sheetType.id, isDeleted=False).count()
        return sheet_type_dict(sheetType, count), 201 if created else 200


# --- Áreas ---

def area_dict(area, sheetCount=0):
    return {"id": str(area.id), "name": area.name, "sort": area.sort, "status": area.status,
            "sheetCount": sheetCount}


class AreaAdminService(object):

    def get(self, areaId):
        areaId = object_id(areaId)
        return areaId and VademecumArea.objects(id=areaId, isDeleted=False).first()

    def list(self):
        counts = _sheet_counts("areas")
        areas = VademecumArea.objects(isDeleted=False).order_by("sort", "name")
        return {"records": [area_dict(a, counts.get(a.id, 0)) for a in areas]}, 200

    def create(self, jsonData):
        return self._save(VademecumArea(), jsonData, created=True)

    def update(self, area, jsonData):
        return self._save(area, jsonData)

    def _save(self, area, jsonData, created=False):
        try:
            data = AreaInputSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        area.name, area.sort, area.status = data["name"], data["sort"], data["status"]
        try:
            area.save()
        except NotUniqueError:
            return {"name": DUPLICATED}, 400
        count = VademecumSheet.objects(areas=area.id, isDeleted=False).count()
        return area_dict(area, count), 201 if created else 200

    def delete(self, area):
        """Borrado lógico; se quita de las fichas que la usan."""
        area.isDeleted = True
        area.save()
        VademecumSheet.objects(areas=area.id).update(pull__areas=area.id)
        return "", 204

