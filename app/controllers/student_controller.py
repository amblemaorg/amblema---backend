# app/controllers/student_controller.py


from flask import request
from flask_restful import Resource

from app.services.student_service import StudentService
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class StudentController(Resource):

    service = StudentService()

    @jwt_required
    def post(self, pecaId, sectionId):
        jsonData = request.get_json()
        return self.service.save(
            pecaId=pecaId,
            sectionId=sectionId,
            jsonData=jsonData)


class StudentHandlerController(Resource):

    service = StudentService()

    @jwt_required
    def put(self, pecaId, sectionId, studentId):
        jsonData = request.get_json()
        return self.service.update(
            pecaId=pecaId,
            sectionId=sectionId,
            studentId=studentId,
            jsonData=jsonData)

    @jwt_required
    def delete(self, pecaId, sectionId, studentId):
        return self.service.delete(
            pecaId=pecaId, sectionId=sectionId, studentId=studentId)
