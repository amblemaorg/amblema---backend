# -*- coding: utf-8 -*-
# app/controllers/vademecum/catalog_controller.py
"""Catálogo público: /vademecum/catalog-options, /vademecum/sheets y sus imágenes."""

import os

from flask import current_app, request, send_from_directory
from flask_restful import Resource

from app.services.vademecum.catalog_service import CatalogService, not_found

IMAGE_MAX_AGE = 60 * 60 * 24 * 365  # la URL lleva ?v=, así que la caché puede ser larga


class CatalogOptionsController(Resource):
    def get(self):
        return CatalogService().catalog_options()


class SheetListController(Resource):
    def get(self):
        return CatalogService().list_sheets(request.args)


class SheetDetailController(Resource):
    def get(self, sheetId):
        return CatalogService().sheet_detail(sheetId)


def _send_image(sheetId, kind):
    storage = current_app.config.get("VADEMECUM_STORAGE_PATH")
    relative = CatalogService().image_path(sheetId, kind)
    if not storage or not relative:
        return not_found()
    root = os.path.realpath(storage)
    path = os.path.realpath(os.path.join(root, relative))
    # La ruta viene de la BD, pero nunca se sirve nada fuera del almacenamiento
    if not path.startswith(root + os.sep) or not os.path.isfile(path):
        return not_found()
    response = send_from_directory(os.path.dirname(path), os.path.basename(path),
                                   mimetype="image/webp", cache_timeout=IMAGE_MAX_AGE)
    response.headers["Cache-Control"] = "public, max-age={}".format(IMAGE_MAX_AGE)
    return response


class SheetThumbnailController(Resource):
    def get(self, sheetId):
        return _send_image(sheetId, "thumbnail")


class SheetPreviewController(Resource):
    def get(self, sheetId):
        return _send_image(sheetId, "preview")
