# -*- coding: utf-8 -*-
# app/services/vademecum/taxonomy_admin_service.py
"""Administración de tipos de ficha y áreas (API-12, GES-03)."""

from datetime import datetime

from marshmallow import ValidationError
from mongoengine.errors import NotUniqueError
from mongoengine.errors import ValidationError as ModelValidationError
from pymongo import UpdateOne

from app.models.vademecum import VademecumArea, VademecumSheet, VademecumSheetType
from app.models.vademecum.sheet_model import build_sheet_code
from app.schemas.vademecum.admin_schema import AreaInputSchema, SheetTypeInputSchema
from app.services.vademecum.catalog_service import object_id
from app.services.vademecum.ref_cache import ref_id, refs

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
        self._apply(sheetType, data)
        return self._save(sheetType, created=True)

    def update(self, sheetType, jsonData):
        try:
            data = SheetTypeInputSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        before = sheetType.codePrefix
        self._apply(sheetType, data)
        response = self._save(sheetType)
        if response[1] == 200 and sheetType.codePrefix != before:
            # El código de la ficha sale del prefijo: se recalcula como en clean(), pero en un
            # solo viaje. `code` depende del número de cada ficha: hace falta un UpdateOne por ficha.
            now = datetime.utcnow()
            sheets = VademecumSheet.objects(sheetType=sheetType.id, isDeleted=False)\
                .only("id", "number")
            operations = [UpdateOne(
                {"_id": sheet.id},
                {"$set": {"code": build_sheet_code(sheetType.codePrefix, sheet.number),
                          "updatedAt": now}})
                for sheet in sheets]
            if operations:
                VademecumSheet._get_collection().bulk_write(operations, ordered=False)
        return response

    def delete(self, sheetType):
        if VademecumSheet.objects(sheetType=sheetType.id, isDeleted=False).first():
            return IN_USE
        sheetType.isDeleted = True
        sheetType.save()
        # Las áreas dejan de ofrecerse para el tipo borrado
        VademecumArea.objects(sheetTypes=sheetType.id).update(pull__sheetTypes=sheetType.id)
        return "", 204

    def _apply(self, sheetType, data):
        for field in ("name", "headerName", "codePrefix", "color", "sectionTitle",
                      "sectionText", "sort", "status"):
            setattr(sheetType, field, data[field])
        sheetType.codePrefix = data["codePrefix"].upper()

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

def area_dict(area, sheetCount=0, typesById=None):
    """`typesById` resuelve todos los tipos del listado en una sola consulta."""
    if typesById is None:
        typesById = refs(VademecumSheetType, area.sheetTypes, ("id", "name"))
    sheetTypes = []
    for ref in area.sheetTypes:
        typeId = ref_id(ref)
        sheetType = typesById.get(str(typeId)) if typeId is not None else None
        if sheetType:
            sheetTypes.append({"id": str(sheetType.id), "name": sheetType.name})
    return {"id": str(area.id), "name": area.name, "sort": area.sort, "status": area.status,
            "sheetCount": sheetCount, "sheetTypes": sheetTypes}


class AreaAdminService(object):

    def get(self, areaId):
        areaId = object_id(areaId)
        return areaId and VademecumArea.objects(id=areaId, isDeleted=False).first()

    def list(self):
        counts = _sheet_counts("areas")
        areas = list(VademecumArea.objects(isDeleted=False).order_by("sort", "name"))
        typesById = refs(VademecumSheetType,
                         [t for area in areas for t in area.sheetTypes], ("id", "name"))
        return {"records": [area_dict(a, counts.get(a.id, 0), typesById) for a in areas]}, 200

    def create(self, jsonData):
        return self._save(VademecumArea(), jsonData, created=True)

    def update(self, area, jsonData):
        return self._save(area, jsonData)

    def _save(self, area, jsonData, created=False):
        try:
            data = AreaInputSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        typeIds = [object_id(t) for t in data["sheetTypeIds"]]
        sheetTypes = list(VademecumSheetType.objects(id__in=[t for t in typeIds if t],
                                                     isDeleted=False))
        if not all(typeIds) or len(sheetTypes) != len(set(typeIds)):
            return {"sheetTypeIds": [{"status": "1", "msg": "Invalid field"}]}, 400
        area.name, area.sort, area.status = data["name"], data["sort"], data["status"]
        area.sheetTypes = sheetTypes
        try:
            area.save()
        except NotUniqueError:
            return {"name": DUPLICATED}, 400
        if area.id:
            # Si deja de servir para un tipo, se quita de las fichas de ese tipo (como al borrar)
            VademecumSheet.objects(areas=area.id, sheetType__nin=[t.id for t in sheetTypes]) \
                .update(pull__areas=area.id)
        count = VademecumSheet.objects(areas=area.id, isDeleted=False).count()
        return area_dict(area, count), 201 if created else 200

    def delete(self, area):
        """Borrado lógico; se quita de las fichas que la usan."""
        area.isDeleted = True
        area.save()
        VademecumSheet.objects(areas=area.id).update(pull__areas=area.id)
        return "", 204

