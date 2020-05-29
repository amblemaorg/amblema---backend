# app/controllers/request_content_approval_controller.py


from flask import request, current_app
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.request_content_approval_model import RequestContentApproval
from app.schemas.request_content_approval_schema import RequestContentApprovalSchema
from app.helpers.handler_request import getQueryParams


class ReqContentApprovalController(Resource):
    service = GenericServices(
        Model=RequestContentApproval,
        Schema=RequestContentApprovalSchema
    )

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(
            filters=filters)


class ReqContentApprovalHandlerController(Resource):
    service = GenericServices(
        Model=RequestContentApproval,
        Schema=RequestContentApprovalSchema
    )

    def get(self, id):
        return self.service.getRecord(id)

    def put(self, id):
        jsonData = request.form.to_dict()
        return self.service.updateRecord(
            recordId=id,
            jsonData=jsonData,
            files=request.files,
            partial=True)

    def delete(self, id):
        return self.service.deleteRecord(id)
