# -*- coding: utf-8 -*-
# app/services/vademecum/sheet_admin_service.py
"""Administración de fichas y textos del sitio (API-12, GES-03).

Las fichas nunca se borran de verdad: el borrado es lógico y las descargas registradas se
conservan. Despublicar deja de entregar la ficha, incluso como redescarga.
"""

import json
import logging
import math
import re
from datetime import datetime

from marshmallow import ValidationError
from mongoengine.errors import NotUniqueError
from mongoengine.errors import ValidationError as ModelValidationError

from app.helpers.vademecum_html import sanitize_html
from app.models.vademecum import (
    VademecumArea, VademecumSheet, VademecumSheetType, VademecumSiteContent)
from app.models.vademecum.constants import SHEET_STATUSES
from app.schemas.vademecum.admin_schema import (
    SheetCreateSchema, SheetIdsSchema, SheetInputSchema, SiteContentInputSchema)
from app.services.vademecum.catalog_service import (
    DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, CatalogService, invalid, isoformat, object_id)
from app.services.vademecum.taxonomy_admin_service import _model_errors
from app.services.vademecum.pdf_upload import ReceivedPdf

logger = logging.getLogger(__name__)

DUPLICATED_SHEET = ({"number": [{"status": "112",
                                 "msg": "Duplicated sheet for type, series and number"}]}, 409)
MAX_QUERY_LENGTH = 100


class SheetAdminService(object):

    def get(self, sheetId):
        sheetId = object_id(sheetId)
        return sheetId and VademecumSheet.objects(id=sheetId, isDeleted=False).first()

    def to_dict(self, sheet, types=None, areas=None):
        catalog = CatalogService()
        if types is None:
            types, areas = catalog._types_and_areas()
        data = catalog.summary(sheet, types, areas)
        data.update({
            "description": sheet.description,
            "pageCount": sheet.file.pageCount if sheet.file else None,
            "sizeBytes": sheet.file.sizeBytes if sheet.file else None,
            "fileReplacedAt": isoformat(sheet.fileReplacedAt),
            "status": sheet.status,
            "downloadCount": sheet.downloadCount,
            "fileStatus": "ready" if sheet.file else None,
            "createdAt": isoformat(sheet.createdAt),
            "updatedAt": isoformat(sheet.updatedAt),
        })
        return data

    def list(self, args):
        query = {"isDeleted": False}
        status = args.get("status")
        if status:
            if status not in SHEET_STATUSES:
                return invalid("status")
            query["status"] = status
        for param, field in (("sheetTypeId", "sheetType"), ("seriesId", "seriesId")):
            value = args.get(param)
            if value:
                query[field] = object_id(value)
                if not query[field]:
                    return invalid(param)
        q = (args.get("q") or "").strip()
        if len(q) > MAX_QUERY_LENGTH:
            return {"q": [{"status": "13", "msg": "Invalid length"}]}, 400
        try:
            page = int(args.get("page") or 1)
            pageSize = int(args.get("pageSize") or DEFAULT_PAGE_SIZE)
        except ValueError:
            return invalid("page")
        if page < 1 or not 1 <= pageSize <= MAX_PAGE_SIZE:
            return invalid("pageSize" if page >= 1 else "page")

        sheets = VademecumSheet.objects(**query)
        if q:
            pattern = {"$regex": re.escape(q), "$options": "i"}
            sheets = sheets.filter(__raw__={"$or": [{"code": pattern}, {"title": pattern}]})
        sheets = sheets.exclude("searchText").order_by("sheetType", "seriesId", "number")
        total = sheets.count()
        types, areas = CatalogService()._types_and_areas()
        records = sheets.skip((page - 1) * pageSize).limit(pageSize)
        return {
            "records": [self.to_dict(s, types, areas) for s in records],
            "pagination": {"page": page, "pageSize": pageSize, "total": total,
                           "pages": int(math.ceil(float(total) / pageSize))},
        }, 200

    def update(self, sheet, jsonData):
        try:
            data = SheetInputSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        failure = self._apply(sheet, data)
        if failure:
            return failure
        if sheet.status == "published":
            # Una ficha publicada no puede quedar sin lo que exige la publicación
            errors = sheet.publish_errors()
            if errors:
                return errors, 400
        return self._save(sheet)

    def _apply(self, sheet, data):
        """Pasa los datos validados a la ficha; devuelve un error o None."""
        if "sheetTypeId" in data:
            typeId = object_id(data["sheetTypeId"])
            sheetType = typeId and VademecumSheetType.objects(id=typeId, isDeleted=False).first()
            if not sheetType:
                return invalid("sheetTypeId")
            sheet.sheetType = sheetType
        if "seriesId" in data:
            if data["seriesId"]:
                seriesId = object_id(data["seriesId"])
                if not seriesId:
                    return invalid("seriesId")
                sheet.seriesId = seriesId
            else:
                sheet.seriesId = None
        if "areaIds" in data:
            ids = [object_id(a) for a in data["areaIds"]]
            if not all(ids):
                return invalid("areaIds")
            areas = list(VademecumArea.objects(id__in=ids, isDeleted=False))
            if len(areas) != len(set(ids)):
                return invalid("areaIds")
            sheet.areas = areas
        for field in ("number", "title", "description", "grades"):
            if field in data:
                setattr(sheet, field, data[field])
        return None

    def create(self, fileStorage, form):
        """Crea una ficha con el PDF que el backoffice separó del compendio (API-11 rehecho).

        Multipart: `file` (PDF de la ficha) y `data` (JSON con número, título, tipo, serie,
        áreas, grados y descripción). `publish=true` la publica al crearla; si faltan datos
        para publicar responde 113 sin crear nada. Se comprime y se generan miniatura, vista
        previa y texto en la misma petición (una ficha son pocas páginas). 201 con la ficha.
        """
        from app.services.vademecum import sheet_media
        try:
            raw = json.loads(form.get("data") or "{}")
        except ValueError:
            return invalid("data", "Invalid JSON")
        try:
            data = SheetCreateSchema().load(raw if isinstance(raw, dict) else {})
        except ValidationError as err:
            return err.messages, 400
        publish = (form.get("publish") or "").lower() == "true"

        sheet = VademecumSheet()
        failure = self._apply(sheet, data)
        if failure:
            return failure
        try:
            sheet.validate()  # tipo y serie coherentes antes de recibir el archivo
        except ModelValidationError as exc:
            return _model_errors(exc)
        if publish:
            errors = {field: value for field, value in sheet.publish_errors().items()
                      if field != "file"}
            if errors:
                return errors, 400
        if VademecumSheet.objects(__raw__={
                "sheetType": sheet.sheetType.id, "seriesId": sheet.seriesId,
                "number": sheet.number, "isDeleted": False}).first():
            return DUPLICATED_SHEET

        with ReceivedPdf(fileStorage) as received:
            if received.failure:
                return received.failure
            body, status = self._save(sheet)
            if status != 200:
                return body, status
            try:
                sheet.file, sheet.searchText = sheet_media.build_sheet_files(
                    received.path, sheet.id)
            except Exception:
                sheet.delete()  # recién creada y sin archivos: no queda a medias
                raise
        if publish:
            sheet.status = "published"
            sheet.publishedAt = datetime.utcnow()
        sheet.save()
        return self.to_dict(sheet), 201

    def _save(self, sheet):
        try:
            sheet.save()
        except NotUniqueError:
            return DUPLICATED_SHEET
        except ModelValidationError as exc:
            return _model_errors(exc)
        return self.to_dict(sheet), 200

    def replace_file(self, sheet, fileStorage):
        """Reemplaza el PDF y regenera miniatura, vista previa y texto (API-10).

        Una ficha son pocas páginas: se genera en la misma petición. Responde 202 como dice el
        contrato; la ficha que devuelve ya tiene los archivos nuevos.
        """
        from app.services.vademecum import sheet_media
        with ReceivedPdf(fileStorage) as received:
            if received.failure:
                return received.failure
            sheetFile, searchText = sheet_media.build_sheet_files(received.path, sheet.id)
        sheet.file = sheetFile
        sheet.searchText = searchText
        sheet.fileReplacedAt = datetime.utcnow()
        body, status = self._save(sheet)
        return body, (202 if status == 200 else status)

    def delete(self, sheet):
        sheet.isDeleted = True
        sheet.save()
        return "", 204

    def publish(self, sheet):
        errors = sheet.publish_errors()
        if errors:
            return errors, 400
        if sheet.status != "published":
            sheet.status = "published"
            # Volver a publicar no la convierte en "nueva": se conserva la primera fecha
            sheet.publishedAt = sheet.publishedAt or datetime.utcnow()
        return self._save(sheet)

    def unpublish(self, sheet):
        if sheet.status == "published":
            sheet.status = "unpublished"
        return self._save(sheet)

    def publish_many(self, jsonData):
        try:
            data = SheetIdsSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        published, failed = [], []
        for sheetId in data["sheetIds"]:
            sheet = self.get(sheetId)
            if not sheet:
                failed.append({"sheetId": sheetId, "errors": {
                    "general": [{"status": "5", "msg": "Record not found"}]}})
                continue
            body, status = self.publish(sheet)
            if status == 200:
                published.append(str(sheet.id))
            else:
                failed.append({"sheetId": str(sheet.id), "errors": body})
        return {"published": published, "failed": failed}, 200


def site_content_dict(content):
    return {"key": content.key, "title": content.title, "body": content.body,
            "updatedAt": isoformat(content.updatedAt)}


class SiteContentAdminService(object):

    def list(self):
        return {"records": [site_content_dict(c)
                            for c in VademecumSiteContent.objects.order_by("key")]}, 200

    def update(self, key, jsonData, admin):
        content = VademecumSiteContent.objects(key=key).first()
        if not content:
            return {"general": [{"status": "5", "msg": "Record not found"}]}, 404
        try:
            data = SiteContentInputSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        content.title = data["title"]
        content.body = sanitize_html(data["body"])
        content.updatedBy = admin
        content.save()
        return site_content_dict(content), 200
