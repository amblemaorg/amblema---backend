# -*- coding: utf-8 -*-
# app/controllers/vademecum/admin_controller.py
"""Administración del backoffice: tipos, áreas, fichas y textos del sitio (API-12)."""

from flask import g, request, send_file
from flask_restful import Resource

from app.helpers.vademecum_auth import vademecum_admin_required
from app.services.vademecum.catalog_service import not_found
from app.services.vademecum.download_service import download_filename, pdf_path
from app.services.vademecum.sheet_admin_service import (
    SheetAdminService, SiteContentAdminService)
from app.services.vademecum.pdf_upload import body_too_large, too_large
from app.services.vademecum.taxonomy_admin_service import (
    AreaAdminService, SheetTypeAdminService)


class AdminSheetTypeListController(Resource):
    @vademecum_admin_required
    def get(self):
        return SheetTypeAdminService().list()

    @vademecum_admin_required
    def post(self):
        return SheetTypeAdminService().create(request.get_json(silent=True))


class AdminSheetTypeController(Resource):
    @vademecum_admin_required
    def put(self, sheetTypeId):
        service = SheetTypeAdminService()
        sheetType = service.get(sheetTypeId)
        if not sheetType:
            return not_found()
        return service.update(sheetType, request.get_json(silent=True))

    @vademecum_admin_required
    def delete(self, sheetTypeId):
        service = SheetTypeAdminService()
        sheetType = service.get(sheetTypeId)
        if not sheetType:
            return not_found()
        return service.delete(sheetType)


class AdminAreaListController(Resource):
    @vademecum_admin_required
    def get(self):
        return AreaAdminService().list()

    @vademecum_admin_required
    def post(self):
        return AreaAdminService().create(request.get_json(silent=True))


class AdminAreaController(Resource):
    @vademecum_admin_required
    def put(self, areaId):
        service = AreaAdminService()
        area = service.get(areaId)
        if not area:
            return not_found()
        return service.update(area, request.get_json(silent=True))

    @vademecum_admin_required
    def delete(self, areaId):
        service = AreaAdminService()
        area = service.get(areaId)
        if not area:
            return not_found()
        return service.delete(area)


class AdminSheetListController(Resource):
    @vademecum_admin_required
    def get(self):
        return SheetAdminService().list(request.args)

    @vademecum_admin_required
    def post(self):
        """Crea una ficha con su PDF ya separado en el backoffice (API-11 rehecho)."""
        if body_too_large(request):
            return too_large()
        return SheetAdminService().create(request.files.get("file"), request.form)


class AdminSheetPublishManyController(Resource):
    @vademecum_admin_required
    def post(self):
        return SheetAdminService().publish_many(request.get_json(silent=True))


def _with_sheet(sheetId, action):
    service = SheetAdminService()
    sheet = service.get(sheetId)
    if not sheet:
        return not_found()
    return action(service, sheet)


class AdminSheetController(Resource):
    @vademecum_admin_required
    def get(self, sheetId):
        return _with_sheet(sheetId, lambda s, sheet: (s.to_dict(sheet), 200))

    @vademecum_admin_required
    def put(self, sheetId):
        data = request.get_json(silent=True)
        return _with_sheet(sheetId, lambda s, sheet: s.update(sheet, data))

    @vademecum_admin_required
    def delete(self, sheetId):
        return _with_sheet(sheetId, lambda s, sheet: s.delete(sheet))


class AdminSheetPublishController(Resource):
    @vademecum_admin_required
    def post(self, sheetId):
        return _with_sheet(sheetId, lambda s, sheet: s.publish(sheet))


class AdminSheetUnpublishController(Resource):
    @vademecum_admin_required
    def post(self, sheetId):
        return _with_sheet(sheetId, lambda s, sheet: s.unpublish(sheet))


class AdminSheetFileController(Resource):
    @vademecum_admin_required
    def get(self, sheetId):
        """PDF para revisar desde el backoffice; no registra descarga."""
        sheet = SheetAdminService().get(sheetId)
        path = pdf_path(sheet) if sheet else None
        if not path:
            return not_found()
        response = send_file(path, mimetype="application/pdf",
                             attachment_filename=download_filename(sheet), cache_timeout=0)
        response.headers["Cache-Control"] = "private, no-store"
        return response

    @vademecum_admin_required
    def put(self, sheetId):
        """Reemplaza el PDF de la ficha (API-10)."""
        if body_too_large(request):
            return too_large()
        return _with_sheet(sheetId, lambda s, sheet: s.replace_file(
            sheet, request.files.get("file")))


class AdminSiteContentListController(Resource):
    @vademecum_admin_required
    def get(self):
        return SiteContentAdminService().list()


class AdminSiteContentController(Resource):
    @vademecum_admin_required
    def put(self, key):
        return SiteContentAdminService().update(key, request.get_json(silent=True),
                                                g.vademecum_admin)
