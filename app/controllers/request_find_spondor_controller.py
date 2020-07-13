# app/controllers/request_find_sponsor_controller.py


from flask import request, current_app
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.request_find_sponsor_model import RequestFindSponsor
from app.schemas.request_find_sponsor_schema import ReqFindSponsorSchema
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class ReqFindSponsorController(Resource):
    service = GenericServices(
        Model=RequestFindSponsor,
        Schema=ReqFindSponsorSchema
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


class ReqFindSponsorHandlerController(Resource):
    service = GenericServices(
        Model=RequestFindSponsor,
        Schema=ReqFindSponsorSchema
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
