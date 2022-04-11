# app/controllers/peca_grade_controller.py

from flask import request
from flask_restful import Resource

from app.services.peca_grade_service import PecaGradeService

class PecaGradeController(Resource):
    service = PecaGradeService()
    def get(self, pecaId):
        return self.service.get(pecaId)
    
    def post(self, pecaId):
        jsonData = request.get_json()
        return self.service.post(pecaId, jsonData)
    
    def patch(self, pecaId):
        jsonData = request.get_json()
        return self.service.deleteStudent(pecaId, jsonData)
    
    def put(self, pecaId):
        jsonData = request.get_json()
        return self.service.changeStatus(pecaId, jsonData)
    