# app/controllers/peca_annual_convention_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_annual_convention_service import AnnualConventionService


class PecaConventionController(Resource):

    service = AnnualConventionService()

    def get(self, pecaId):
        return self.service.get(pecaId)

    def post(self, pecaId):
        jsonData = request.get_json()
        return self.service.save(pecaId, jsonData)
