# app/controllers/request_project_approval_controller.py


from flask import request, current_app
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.request_project_approval_model import RequestProjectApproval
from app.schemas.request_project_approval_schema import RequestProjectApprovalSchema
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required
from app.helpers.school_year_filter import get_school_year_date_filters


class ReqProjectApprovalController(Resource):
    service = GenericServices(
        Model=RequestProjectApproval,
        Schema=RequestProjectApprovalSchema
    )

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        if not filters:
            filters = []
        filters.extend(get_school_year_date_filters())
        
        only = None
        if 'only' in request.args:
            only = request.args['only'].split(',')
        return self.service.getAllRecords(
            filters=filters, only=only)


class ReqProjectApprovalHandlerController(Resource):
    service = GenericServices(
        Model=RequestProjectApproval,
        Schema=RequestProjectApprovalSchema
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
            files=request.files,
            partial=True)

    @jwt_required
    def delete(self, id):
        return self.service.deleteRecord(id)
