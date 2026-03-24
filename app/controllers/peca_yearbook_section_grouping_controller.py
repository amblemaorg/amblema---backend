# app/controllers/peca_yearbook_section_grouping_controller.py

from flask import request
from flask_restful import Resource

from app.services.peca_yearbook_service import YearbookService

class PecaYearbookSectionGroupingController(Resource):

    service = YearbookService()

    def patch(self, pecaId):
        jsonData = request.get_json()
        return self.service.save_section_grouping(pecaId, jsonData)

    def get(self, pecaId):
        return self.service.get_section_grouping(pecaId)
