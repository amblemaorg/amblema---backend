# app/controllers/request_content_approval_controller.py


from flask import request, current_app
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.request_content_approval_model import RequestContentApproval
from app.schemas.request_content_approval_schema import RequestContentApprovalSchema
from app.services.request_content_approval_service import RequestContentApprovalService
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required
from app.helpers.school_year_filter import get_school_year_date_filters


class ReqContentApprovalController(Resource):
    service = RequestContentApprovalService(
        Model=RequestContentApproval,
        Schema=RequestContentApprovalSchema
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
        
        page = request.args.get('page')
        per_page = request.args.get('per_page')

        if page and per_page:
            new_filters = []
            for f in filters:
                if f['field'] == 'page' or f['field'] == 'per_page':
                    continue
                new_filters.append(f)
            return self.service.getPaginatedData(
                filters=new_filters,
                page=int(page),
                page_size=int(per_page)
            )

        return self.service.getAllRecords(
            filters=filters, only=only)


class ReqContentApprovalHandlerController(Resource):
    service = RequestContentApprovalService(
        Model=RequestContentApproval,
        Schema=RequestContentApprovalSchema
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
