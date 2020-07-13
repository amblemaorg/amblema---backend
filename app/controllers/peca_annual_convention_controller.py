# app/controllers/peca_annual_convention_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_annual_convention_service import AnnualConventionService
from app.helpers.handler_authorization import jwt_required


class PecaConventionController(Resource):

    service = AnnualConventionService()

    @jwt_required
    def get(self, pecaId):
        return self.service.get(pecaId)

    @jwt_required
    def post(self, pecaId):
        jsonData = request.get_json()
        return self.service.save(pecaId, jsonData)
