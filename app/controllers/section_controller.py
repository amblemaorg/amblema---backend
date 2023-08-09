# app/controllers/section_controller.py


from flask import request
from flask_restful import Resource

from app.services.section_service import SectionService, SectionsImportExport
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class SectionController(Resource):

    service = SectionService()

    @jwt_required
    def post(self, pecaId):
        jsonData = request.get_json()
        return self.service.save(pecaId=pecaId, jsonData=jsonData)


class SectionHandlerController(Resource):

    service = SectionService()

    @jwt_required
    def put(self, pecaId, sectionId):
        jsonData = request.get_json()
        return self.service.update(
            pecaId=pecaId,
            sectionId=sectionId,
            jsonData=jsonData)

    @jwt_required
    def delete(self, pecaId, sectionId):
        return self.service.delete(pecaId=pecaId, sectionId=sectionId)

class SectionsImportExportController(Resource):
    service = SectionsImportExport()
    def post(self, pecaId):
        jsonData = request.get_json()
        return self.service.loadSections(pecaId=pecaId,jsonData=jsonData)