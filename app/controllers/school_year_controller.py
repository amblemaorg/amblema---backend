# /app/controllers/role_controller.py


from flask import request
from flask_restful import Resource

from app.services.school_year_service import SchoolYearService
from app.models.school_year_model import SchoolYear
from app.schemas.school_year_schema import SchoolYearSchema
from app.helpers.handler_request import getQueryParams


class SchoolYearController(Resource):

    service = SchoolYearService(
        Model=SchoolYear,
        Schema=SchoolYearSchema)

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class SchoolYearHandlerController(Resource):

    service = SchoolYearService(
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


class EnrollCtrl(Resource):

    service = SchoolYearService(
        Model=SchoolYear,
        Schema=SchoolYearSchema)

    def put(self, projectId):
        action = request.args.get('action')
        return self.service.schoolEnroll(
            projectId=projectId,
            action=action)


class EnrollSchoolsCtrl(Resource):
    service = SchoolYearService(
        Model=SchoolYear,
        Schema=SchoolYearSchema
    )

    def get(self):
        return self.service.availableSchools()
