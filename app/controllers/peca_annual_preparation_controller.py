# app/controllers/peca_annual_preparation_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_annual_preparation_service import AnnualPreparationService


class PecaPreparationController(Resource):

    service = AnnualPreparationService()

    def get(self, pecaId):
        return self.service.get(pecaId)

    def post(self, pecaId):
        jsonData = request.get_json()
        return self.service.save(pecaId, jsonData)


class PecaPreparationHandlerCtrl(Resource):
    service = AnnualPreparationService()

    def put(self, pecaId, teacherId):
        jsonData = request.get_json()
        return self.service.update(pecaId, teacherId, jsonData)
