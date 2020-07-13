# app/controllers/teacher_controller.py


from flask import request
from flask_restful import Resource

from app.services.teacher_service import TeacherService
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class TeacherController(Resource):

    service = TeacherService()

    @jwt_required
    def post(self, schoolId):
        jsonData = request.get_json()
        return self.service.save(schoolId=schoolId, jsonData=jsonData)

    @jwt_required
    def get(self, schoolId):
        return self.service.getAll(schoolId)


class TeacherHandlerController(Resource):

    service = TeacherService()

    @jwt_required
    def put(self, schoolId, teacherId):
        jsonData = request.get_json()
        return self.service.update(
            schoolId=schoolId,
            teacherId=teacherId,
            jsonData=jsonData)

    @jwt_required
    def delete(self, schoolId, teacherId):
        return self.service.delete(schoolId=schoolId, teacherId=teacherId)
