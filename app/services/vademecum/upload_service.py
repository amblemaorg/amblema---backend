# -*- coding: utf-8 -*-
# app/services/vademecum/upload_service.py
"""Carga de compendios PDF y su seguimiento (API-07, GES-03 5.5).

El original se guarda en `uploads/<uploadId>/original.pdf` dentro de VADEMECUM_STORAGE_PATH
(nunca en `resources/`) y se conserva para reprocesar. Aquí solo se recibe y valida el
archivo; el procesamiento en segundo plano es de API-08.
"""

import logging
import math
import os
import shutil
import uuid
from datetime import datetime

from flask import current_app

from app.models.vademecum import VademecumSheet, VademecumSheetType, VademecumUpload
from app.models.vademecum.constants import UPLOAD_STATUSES
from app.services.vademecum import processing_service
from app.services.vademecum.catalog_service import (
    DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, invalid, isoformat, not_found, object_id, series_dict)

logger = logging.getLogger(__name__)

DEFAULT_MAX_UPLOAD_MB = 100
# El encabezado %PDF- puede estar en cualquier parte del primer KB (especificación PDF)
PDF_SIGNATURE = b"%PDF-"
PDF_HEADER_WINDOW = 1024
CHUNK_SIZE = 1024 * 1024
# `uploaded` se puede borrar: el hilo que la tome no escribe sobre una carga borrada
BUSY_STATUSES = ("processing", "generating")
MAX_FILENAME_LENGTH = 255
# Margen para los campos y separadores del multipart sobre el tamaño del PDF
MULTIPART_OVERHEAD_BYTES = 64 * 1024


def error(field, code, msg, httpStatus=400):
    return {field: [{"status": code, "msg": msg}]}, httpStatus


def max_upload_bytes():
    try:
        megabytes = int(current_app.config.get("VADEMECUM_MAX_UPLOAD_MB")
                        or DEFAULT_MAX_UPLOAD_MB)
    except (TypeError, ValueError):
        megabytes = DEFAULT_MAX_UPLOAD_MB
    return megabytes * 1024 * 1024


def storage_root():
    storage = current_app.config.get("VADEMECUM_STORAGE_PATH")
    return os.path.realpath(storage) if storage else None


def upload_dir(root, uploadId):
    return os.path.join(root, "uploads", str(uploadId))


def too_large():
    return error("file", "115", "File must be a PDF up to {} MB".format(
        max_upload_bytes() // (1024 * 1024)))


class InvalidPdf(Exception):
    pass


def save_pdf_stream(stream, target, maxBytes):
    """Copia el archivo por bloques validando firma y tamaño; devuelve los bytes escritos."""
    written = 0
    head = b""
    with open(target, "wb") as handle:
        while True:
            chunk = stream.read(CHUNK_SIZE)
            if not chunk:
                break
            if len(head) < PDF_HEADER_WINDOW:
                head += chunk[:PDF_HEADER_WINDOW - len(head)]
            written += len(chunk)
            if written > maxBytes:
                raise InvalidPdf("too large")
            handle.write(chunk)
    if not written or PDF_SIGNATURE not in head:
        raise InvalidPdf("not a pdf")
    return written


def clean_filename(name):
    name = os.path.basename((name or "").replace("\\", "/")).strip()
    return name[:MAX_FILENAME_LENGTH] or "compendio.pdf"


class UploadService(object):

    # --- Formato ---

    def summary(self, upload):
        sheetType = upload.sheetType
        series = sheetType.get_series(upload.seriesId) if sheetType else None
        user = upload.createdBy
        return {
            "id": str(upload.id),
            "originalFileName": upload.originalFileName,
            "originalSizeBytes": upload.originalSizeBytes,
            "pageCount": upload.pageCount,
            "sheetType": ({"id": str(sheetType.id), "name": sheetType.name,
                           "codePrefix": sheetType.codePrefix, "color": sheetType.color}
                          if sheetType else None),
            "series": series_dict(series) if series else None,
            "status": upload.status,
            "progress": upload.progress,
            "errorMessage": upload.errorMessage,
            "sheetCount": len(upload.sheets),
            "createdBy": ({"id": str(user.id), "name": user.name or u"{} {}".format(
                getattr(user, "firstName", u"") or u"", getattr(user, "lastName", u"") or u""
            ).strip()} if user else None),
            "createdAt": isoformat(upload.createdAt),
            "processedAt": isoformat(upload.processedAt),
        }

    def detail(self, upload):
        data = self.summary(upload)
        data["pages"] = [{
            "index": p.index, "headerText": p.headerText, "number": p.number,
            "isContinuation": p.isContinuation, "title": p.title,
            "thumbnailUrl": ("/vademecum/admin/uploads/{}/pages/{}/thumbnail.webp".format(
                upload.id, p.index) if p.thumbnailPath else None),
        } for p in upload.pages]
        data["proposedCuts"] = [self._cut(c) for c in upload.proposedCuts]
        data["confirmedCuts"] = [self._cut(c) for c in upload.confirmedCuts]
        data["sheets"] = [{"id": str(s.id), "code": s.code, "title": s.title}
                          for s in VademecumSheet.objects(
                              id__in=[s.id for s in upload.sheets], isDeleted=False)
                          .only("id", "code", "title")]
        return data

    def _cut(self, cut):
        return {"pages": list(cut.pages), "number": cut.number, "title": cut.title,
                "excluded": cut.excluded}

    def get(self, uploadId):
        uploadId = object_id(uploadId)
        if not uploadId:
            return None
        processing_service.mark_stale()
        return VademecumUpload.objects(id=uploadId, isDeleted=False).first()

    # --- Acciones ---

    def create(self, fileStorage, form, admin):
        """Valida y guarda el compendio; responde 202 con la carga en `uploaded`."""
        sheetType, seriesId, failure = self._sheet_type_and_series(form)
        if failure:
            return failure
        if fileStorage is None or not fileStorage.filename:
            return error("file", "2", "Missing data for required field.")
        root = storage_root()
        if not root:
            logger.error("Vademecum: VADEMECUM_STORAGE_PATH is not configured")
            return error("general", "0", "Storage is not configured", 500)

        maxBytes = max_upload_bytes()

        # Primero a un temporal: la carga solo se crea si el archivo es válido
        uploadsRoot = os.path.join(root, "uploads")
        os.makedirs(uploadsRoot, exist_ok=True)
        temporary = os.path.join(uploadsRoot, "tmp-{}.pdf".format(uuid.uuid4().hex))
        try:
            size = save_pdf_stream(fileStorage.stream, temporary, maxBytes)
        except InvalidPdf:
            _remove(temporary)
            return too_large()

        upload = VademecumUpload(originalFileName=clean_filename(fileStorage.filename),
                                 originalSizeBytes=size, sheetType=sheetType,
                                 seriesId=seriesId, createdBy=admin, status="uploaded",
                                 heartbeatAt=datetime.utcnow())
        try:
            upload.save()
            target = upload_dir(root, upload.id)
            os.makedirs(target, exist_ok=True)
            os.replace(temporary, os.path.join(target, "original.pdf"))
            upload.originalPath = "uploads/{}/original.pdf".format(upload.id)
            upload.save()
        except Exception:
            _remove(temporary)
            if upload.id:
                upload.delete()
                shutil.rmtree(upload_dir(root, upload.id), ignore_errors=True)
            raise
        processing_service.start(upload)
        upload.reload()
        return self.summary(upload), 202

    def reprocess(self, upload):
        """Vuelve a leer el original conservado (API-08); 409 si está ocupada o generada."""
        processing_service.mark_stale()
        if not processing_service.queue_again(upload):
            return error("general", "114", "Upload status does not allow this action", 409)
        processing_service.start(upload)
        upload.reload()
        return self.summary(upload), 202

    def _sheet_type_and_series(self, form):
        sheetTypeId = (form.get("sheetTypeId") or "").strip()
        if not sheetTypeId:
            return None, None, error("sheetTypeId", "2", "Missing data for required field.")
        typeId = object_id(sheetTypeId)
        sheetType = typeId and VademecumSheetType.objects(id=typeId, isDeleted=False).first()
        if not sheetType:
            return None, None, invalid("sheetTypeId")

        rawSeries = (form.get("seriesId") or "").strip()
        if rawSeries:
            series = sheetType.get_series(object_id(rawSeries))
            if not series or series.isDeleted:
                return None, None, invalid("seriesId")
            return sheetType, series.id, None
        if sheetType.active_series():
            return None, None, error("seriesId", "2", "Missing data for required field.")
        return sheetType, None, None

    def list(self, args):
        query = {"isDeleted": False}
        status = args.get("status")
        if status:
            if status not in UPLOAD_STATUSES:
                return invalid("status")
            query["status"] = status
        try:
            page = int(args.get("page") or 1)
            pageSize = int(args.get("pageSize") or DEFAULT_PAGE_SIZE)
        except ValueError:
            return invalid("page")
        if page < 1 or not 1 <= pageSize <= MAX_PAGE_SIZE:
            return invalid("pageSize" if page >= 1 else "page")
        processing_service.mark_stale()
        uploads = VademecumUpload.objects(**query).exclude(
            "pages", "proposedCuts", "confirmedCuts").order_by("-createdAt")
        total = uploads.count()
        records = uploads.skip((page - 1) * pageSize).limit(pageSize)
        return {
            "records": [self.summary(u) for u in records],
            "pagination": {"page": page, "pageSize": pageSize, "total": total,
                           "pages": int(math.ceil(float(total) / pageSize))},
        }, 200

    def delete(self, upload):
        """Borra la carga si ninguna ficha suya se publicó nunca; sus fichas en borrador también."""
        if upload.status in BUSY_STATUSES:
            return error("general", "114", "Upload status does not allow this action", 409)
        sheetIds = [s.id for s in upload.sheets]
        if VademecumSheet.objects(id__in=sheetIds, isDeleted=False,
                                  publishedAt__ne=None).first():
            return error("general", "114", "Upload has published sheets", 409)
        VademecumSheet.objects(id__in=sheetIds, isDeleted=False).update(set__isDeleted=True)
        upload.isDeleted = True
        upload.save()
        root = storage_root()
        if root:
            shutil.rmtree(upload_dir(root, upload.id), ignore_errors=True)
        return "", 204


def _remove(path):
    try:
        os.remove(path)
    except OSError:
        pass
