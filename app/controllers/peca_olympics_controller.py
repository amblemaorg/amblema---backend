# app/controllers/peca_olympics_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_olympics_service import OlympicsService
from app.helpers.handler_authorization import jwt_required


class PecaOlympicsController(Resource):

    service = OlympicsService()

    @jwt_required
    def get(self, pecaId, lapse):
        return self.service.getOlympics(pecaId, lapse)

    @jwt_required
    def post(self, pecaId, lapse):
        jsonData = request.get_json()
        return self.service.saveStudent(pecaId, lapse, jsonData)


class PecaOlympicsHandlerCtrl(Resource):
    service = OlympicsService()

    @jwt_required
    def put(self, pecaId, lapse, studentId):
        jsonData = request.get_json()
        return self.service.updateStudent(pecaId, lapse, studentId, jsonData)

    @jwt_required
    def delete(self, pecaId, lapse, studentId):
        return self.service.deleteStudent(pecaId, lapse, studentId)
