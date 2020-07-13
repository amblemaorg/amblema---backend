# app/controllers/request_content_approval_controller.py


from flask import request, current_app
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.request_content_approval_model import RequestContentApproval
from app.schemas.request_content_approval_schema import RequestContentApprovalSchema
from app.services.request_content_approval_service import RequestContentApprovalService
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class ReqContentApprovalController(Resource):
    service = RequestContentApprovalService(
        Model=RequestContentApproval,
        Schema=RequestContentApprovalSchema
    )

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(
            filters=filters)


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
