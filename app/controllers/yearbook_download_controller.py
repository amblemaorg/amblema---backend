# app/controllers/yearbook_download_controller.py

from flask import request
from flask_restful import Resource

from app.services.yearbook_download_service import YearbookDownloadService
from app.helpers.handler_authorization import jwt_required, admin_required


class YearbookDownloadListController(Resource):

    service = YearbookDownloadService()

    @admin_required
    def get(self):
        return self.service.listActive()


class YearbookDownloadController(Resource):

    service = YearbookDownloadService()

    @jwt_required
    def get(self, id):
        return self.service.get(id)

    @admin_required
    def patch(self, id):
        jsonData = request.get_json(silent=True) or {}
        return self.service.setEnabled(id, jsonData)
