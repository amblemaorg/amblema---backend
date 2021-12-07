# /app/controllers/specialty_teacher_controller.py


from flask import request
from flask_restful import Resource

from app.services.specialty_teacher_service import SpecialtyTeacherService
from app.models.specialty_teacher_model import SpecialtyTeacher
from app.schemas.specialty_teacher_schema import SpecialtyTeacherSchema
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class SpecialtyTeacherController(Resource):

    service = SpecialtyTeacherService(
        Model=SpecialtyTeacher,
        Schema=SpecialtyTeacherSchema)

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    @jwt_required
    def post(self):
        jsonData = request.get_json()
        print(jsonData)
        return self.service.saveRecord(jsonData)


class SpecialtyTeacherHandlerController(Resource):

    service = SpecialtyTeacherService(
        Model=SpecialtyTeacher,
        Schema=SpecialtyTeacherSchema)

    def get(self, specialtyId):
        return self.service.getRecord(specialtyId)

    @jwt_required
    def put(self, specialtyId):
        jsonData = request.get_json()
        return self.service.updateRecord(
            recordId=specialtyId,
            jsonData=jsonData,
            partial=("name",))

    @jwt_required
    def delete(self, specialtyId):
        return self.service.deleteRecord(specialtyId)
