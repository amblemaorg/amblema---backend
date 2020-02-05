# /app/controllers/role_controller.py


from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.school_year_model import (
    SchoolYear, SchoolYearSchema)
from app.helpers.handler_request import getQueryParams


class SchoolYearController(Resource):
    
    service = GenericServices(
        Model=SchoolYear,
        Schema=SchoolYearSchema)

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)

    
class SchoolYearHandlerController(Resource):
    
    service = GenericServices(
        Model=SchoolYear,
        Schema=SchoolYearSchema)

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

