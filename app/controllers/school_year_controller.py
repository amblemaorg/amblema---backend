# /app/controllers/role_controller.py


from flask import request
from flask_restful import Resource

from app.services.school_year_service import (SchoolYearService, CronDiagnosticosService, 
                                              CronAddDiagnosticsService, CronClearApprovalHistoryService, 
                                              ClearApprovalHistoryPastYearService,CronUpdateDataProjectsService,
                                              CronUpdateDataActiviyProjectsService)
from app.models.school_year_model import SchoolYear
from app.schemas.school_year_schema import SchoolYearSchema
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class SchoolYearController(Resource):

    service = SchoolYearService(
        Model=SchoolYear,
        Schema=SchoolYearSchema)

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters, only=('id', 'name', 'status', 'startDate', 'endDate'))

    @jwt_required
    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class SchoolYearHandlerController(Resource):

    service = SchoolYearService(
        Model=SchoolYear,
        Schema=SchoolYearSchema)

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


class EnrollCtrl(Resource):

    service = SchoolYearService(
        Model=SchoolYear,
        Schema=SchoolYearSchema)

    @jwt_required
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

    @jwt_required
    def get(self):
        return self.service.availableSchools()

class CronScrollYearCtrl(Resource):
    service = SchoolYearService(
        Model=SchoolYear,
        Schema=SchoolYearSchema
    )
    def get(self):
        return self.service.updateStastistics()

class CronEmptySchoolCtrl(Resource):
    service = SchoolYearService(
        Model=SchoolYear,
        Schema=SchoolYearSchema
    )
    def get(self):
        return self.service.emptySchools()

class CronDiagnisticosCtrl(Resource):
    service = CronDiagnosticosService()
    def get(self, limit,skip):
        return self.service.run(limit, skip)
        

class CronAddDiagnosticsCtrl(Resource):
    service = CronAddDiagnosticsService()
    def get(self, limit,skip):
        return self.service.run(limit, skip)

class CronClearApprovalHistoryCtrl(Resource):
    service = CronClearApprovalHistoryService()
    def get(self, desde,hasta):
        return self.service.run(desde, hasta)

 
class ClearApprovalHistoryPastYearCtrl(Resource):
    service = ClearApprovalHistoryPastYearService()
    def get(self):
        return self.service.run()
    
class CronUpdateDataProjectsCtrl(Resource):
    service = CronUpdateDataProjectsService()
    def get(self, limit, skip):
        return self.service.run(limit, skip)
    
class CronUpdateDataActivityProjectsCtrl(Resource):
    service = CronUpdateDataActiviyProjectsService()
    def get(self, limit, skip):
        return self.service.run(limit, skip)