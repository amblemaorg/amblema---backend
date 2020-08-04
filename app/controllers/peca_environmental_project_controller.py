# app/controllers/peca_environmental_project_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_environmental_project_service import EnvironmentalProjectPecaService
from app.helpers.handler_authorization import jwt_required


class PecaEnvironmentalProjectCtrl(Resource):

    service = EnvironmentalProjectPecaService()

    @jwt_required
    def post(self, pecaId):
        jsonData = request.get_json()
        return self.service.save(pecaId, jsonData)
