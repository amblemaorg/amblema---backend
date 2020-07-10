# /app/views/municipality.py


from flask import request
from flask_restful import Resource

from app.models.state_model import State, Municipality, MunicipalitySchema
from app.services.municipality_service import MunicipalityService
from app.helpers.handler_request import getQueryParams


class MunicipalityController(Resource):

    service = MunicipalityService(
        Model=Municipality,
        Schema=MunicipalitySchema
    )

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class MunicipalityHandlerController(Resource):

    service = MunicipalityService(
        Model=Municipality,
        Schema=MunicipalitySchema
    )

    def get(self, municipalityId):
        return self.service.getRecord(municipalityId)

    def put(self, municipalityId):
        jsonData = request.get_json()
        return self.service.updateRecord(
            recordId=municipalityId,
            jsonData=jsonData,
            partial=("name", "actions"))

    def delete(self, municipalityId):
        return self.service.deleteRecord(municipalityId)
