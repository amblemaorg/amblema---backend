# app/controllers/diagnostic_controller.py


from flask import request
from flask_restful import Resource

from app.services.diagnostic_service import DiagnosticService
from app.helpers.handler_request import getQueryParams


class DiagnosticController(Resource):

    service = DiagnosticService()

    def post(self, diagnostic, lapse, pecaId, sectionId, studentId):
        jsonData = request.get_json()
        return self.service.save(
            diagnosticType=diagnostic,
            lapse=lapse,
            pecaId=pecaId,
            sectionId=sectionId,
            studentId=studentId,
            jsonData=jsonData)

    def delete(self, diagnostic, lapse, pecaId, sectionId, studentId):
        return self.service.delete(
            diagnosticType=diagnostic,
            lapse=lapse,
            pecaId=pecaId,
            sectionId=sectionId,
            studentId=studentId
        )