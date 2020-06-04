# app/controllers/teacher_controller.py


from flask import request
from flask_restful import Resource

from app.services.teacher_service import TeacherService
from app.helpers.handler_request import getQueryParams


class TeacherController(Resource):

    service = TeacherService()

    def post(self, schoolId):
        jsonData = request.get_json()
        return self.service.save(schoolId=schoolId, jsonData=jsonData)


class TeacherHandlerController(Resource):

    service = TeacherService()

    def put(self, schoolId, teacherId):
        jsonData = request.get_json()
        return self.service.update(
            schoolId=schoolId,
            teacherId=teacherId,
            jsonData=jsonData)

    def delete(self, schoolId, teacherId):
        return self.service.delete(schoolId=schoolId, teacherId=teacherId)
