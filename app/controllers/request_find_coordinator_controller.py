# app/controllers/request_find_coordinator_controller.py


from flask import request, current_app
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.request_find_coordinator_model import RequestFindCoordinator
from app.schemas.request_find_coordinator_schema import ReqFindCoordSchema
from app.helpers.handler_request import getQueryParams


class ReqFindCoordController(Resource):
    service = GenericServices(
        Model=RequestFindCoordinator,
        Schema=ReqFindCoordSchema
    )

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(
            filters=filters)

    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class ReqFindCoordHandlerController(Resource):
    service = GenericServices(
        Model=RequestFindCoordinator,
        Schema=ReqFindCoordSchema
    )

    def get(self, id):
        return self.service.getRecord(id)

    def put(self, id):
        jsonData = request.get_json()
        return self.service.updateRecord(
            recordId=id,
            jsonData=jsonData,
            partial=True)

    def delete(self, id):
        return self.service.deleteRecord(id)
