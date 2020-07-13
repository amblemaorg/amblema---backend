# app/controllers/request_find_school_controller.py


from flask import request, current_app
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.request_find_school_model import RequestFindSchool
from app.schemas.request_find_school_schema import ReqFindSchoolSchema
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class ReqFindSchoolController(Resource):
    service = GenericServices(
        Model=RequestFindSchool,
        Schema=ReqFindSchoolSchema
    )

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(
            filters=filters)

    @jwt_required
    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class ReqFindSchoolHandlerController(Resource):
    service = GenericServices(
        Model=RequestFindSchool,
        Schema=ReqFindSchoolSchema
    )

    @jwt_required
    def get(self, id):
        return self.service.getRecord(id)

    @jwt_required
    def put(self, id):
        jsonData = request.get_json()
        return self.service.updateRecord(
            recordId=id,
            jsonData=jsonData,
            partial=True)

    @jwt_required
    def delete(self, id):
        return self.service.deleteRecord(id)
