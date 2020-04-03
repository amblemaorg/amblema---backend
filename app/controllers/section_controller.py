# app/controllers/section_controller.py


from flask import request
from flask_restful import Resource

from app.services.section_service import SectionService
from app.helpers.handler_request import getQueryParams


class SectionController(Resource):

    service = SectionService()

    def post(self, pecaId):
        jsonData = request.get_json()
        return self.service.save(pecaId=pecaId, jsonData=jsonData)


class SectionHandlerController(Resource):

    service = SectionService()

    def put(self, pecaId, sectionId):
        jsonData = request.get_json()
        return self.service.update(
            pecaId=pecaId,
            sectionId=sectionId,
            jsonData=jsonData)

    def delete(self, pecaId, sectionId):
        return self.service.delete(pecaId=pecaId, sectionId=sectionId)
