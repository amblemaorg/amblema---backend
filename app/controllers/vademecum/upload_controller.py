# -*- coding: utf-8 -*-
# app/controllers/vademecum/upload_controller.py
"""Cargas de compendios del backoffice: /vademecum/admin/uploads (API-07)."""

from flask import g, request, send_file
from flask_restful import Resource

from app.helpers.vademecum_auth import vademecum_admin_required
from app.services.vademecum import generation_service
from app.services.vademecum.catalog_service import not_found
from app.services.vademecum.upload_service import (
    MULTIPART_OVERHEAD_BYTES, UploadService, max_upload_bytes, too_large)


class AdminUploadListController(Resource):
    @vademecum_admin_required
    def get(self):
        return UploadService().list(request.args)

    @vademecum_admin_required
    def post(self):
        # Antes de leer request.files: Werkzeug volcaría a disco un cuerpo de cualquier tamaño
        if (request.content_length or 0) > max_upload_bytes() + MULTIPART_OVERHEAD_BYTES:
            return too_large()
        return UploadService().create(request.files.get("file"), request.form,
                                      g.vademecum_admin)


class AdminUploadController(Resource):
    @vademecum_admin_required
    def get(self, uploadId):
        service = UploadService()
        upload = service.get(uploadId)
        if not upload:
            return not_found()
        return service.detail(upload), 200

    @vademecum_admin_required
    def delete(self, uploadId):
        service = UploadService()
        upload = service.get(uploadId)
        if not upload:
            return not_found()
        return service.delete(upload)


class AdminUploadReprocessController(Resource):
    @vademecum_admin_required
    def post(self, uploadId):
        service = UploadService()
        upload = service.get(uploadId)
        if not upload:
            return not_found()
        return service.reprocess(upload)


class AdminUploadPageThumbnailController(Resource):
    @vademecum_admin_required
    def get(self, uploadId, index):
        """Miniatura de una página para revisar cortes (API-10); se pide como blob con token."""
        service = UploadService()
        upload = service.get(uploadId)
        path = service.page_thumbnail(upload, index) if upload else None
        if not path:
            return not_found()
        response = send_file(path, mimetype="image/webp", cache_timeout=0)
        # Imagen de administrador: el navegador puede guardarla, los proxies no
        response.headers["Cache-Control"] = "private, max-age=300"
        return response


class AdminUploadCutsController(Resource):
    @vademecum_admin_required
    def put(self, uploadId):
        """Guarda los cortes confirmados (API-11)."""
        service = UploadService()
        upload = service.get(uploadId)
        if not upload:
            return not_found()
        return generation_service.save_cuts(upload, request.get_json(silent=True),
                                            service.detail)


class AdminUploadGenerateController(Resource):
    @vademecum_admin_required
    def post(self, uploadId):
        """Genera las fichas en `draft` en segundo plano (API-11)."""
        service = UploadService()
        upload = service.get(uploadId)
        if not upload:
            return not_found()
        return generation_service.generate(upload, service.summary)
