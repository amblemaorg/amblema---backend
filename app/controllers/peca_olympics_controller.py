# app/controllers/peca_olympics_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_olympics_service import OlympicsService
from app.helpers.handler_authorization import jwt_required


class PecaOlympicsController(Resource):

    service = OlympicsService()

    @jwt_required
    def get(self, pecaId, lapse):
        olympicsType = request.args.get('type', 'math')
        return self.service.getOlympics(pecaId, lapse, olympicsType)

    @jwt_required
    def post(self, pecaId, lapse):
        olympicsType = request.args.get('type', 'math')
        jsonData = request.get_json()
        return self.service.saveStudent(pecaId, lapse, jsonData, olympicsType)


class PecaOlympicsHandlerCtrl(Resource):
    service = OlympicsService()

    @jwt_required
    def put(self, pecaId, lapse, studentId):
        olympicsType = request.args.get('type', 'math')
        jsonData = request.get_json()
        return self.service.updateStudent(pecaId, lapse, studentId, jsonData, olympicsType)

    @jwt_required
    def delete(self, pecaId, lapse, studentId):
        olympicsType = request.args.get('type', 'math')
        return self.service.deleteStudent(pecaId, lapse, studentId, olympicsType)
