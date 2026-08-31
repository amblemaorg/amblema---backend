# app/controllers/environmental_diagnostic_controller.py

from flask import request
from flask_restful import Resource

from app.services.environmental_diagnostic_service import EnvironmentalDiagnosticService
from app.helpers.handler_authorization import jwt_required


class EnvironmentalDiagnosticEvaluatorController(Resource):

    service = EnvironmentalDiagnosticService()

    @jwt_required
    def post(self, pecaId, lapse):
        jsonData = request.get_json()
        origin = request.headers.get('Origin')
        return self.service.register_evaluator(pecaId, lapse, jsonData, web_origin=origin, req=request)

    @jwt_required
    def get(self, pecaId, lapse):
        origin = request.headers.get('Origin')
        return self.service.get_evaluators(pecaId, lapse, web_origin=origin, req=request)


class EnvironmentalDiagnosticEvaluationController(Resource):

    service = EnvironmentalDiagnosticService()

    def get(self, token):
        return self.service.get_evaluation(token)

    def post(self, token):
        jsonData = request.get_json()
        return self.service.submit_evaluation(token, jsonData)
