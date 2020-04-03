# app/controllers/teacher_controller.py


from flask import request
from flask_restful import Resource

from app.services.teacher_service import TeacherService
from app.helpers.handler_request import getQueryParams


class TeacherController(Resource):

    service = TeacherService()

    def post(self, pecaId):
        jsonData = request.get_json()
        return self.service.save(pecaId=pecaId, jsonData=jsonData)


class TeacherHandlerController(Resource):

    service = TeacherService()

    def put(self, pecaId, teacherId):
        jsonData = request.get_json()
        return self.service.update(
            pecaId=pecaId,
            teacherId=teacherId,
            jsonData=jsonData)

    def delete(self, pecaId, teacherId):
        return self.service.delete(pecaId=pecaId, teacherId=teacherId)
