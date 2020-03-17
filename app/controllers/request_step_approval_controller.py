# app/controllers/request_step_approval_controller.py


from flask import request, current_app
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.request_step_approval_model import RequestStepApproval
from app.schemas.request_step_approval_schema import RequestStepApprovalSchema
from app.helpers.handler_request import getQueryParams


class ReqStepApprovalController(Resource):
    service = GenericServices(
        Model=RequestStepApproval,
        Schema=RequestStepApprovalSchema
    )

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(
            filters=filters)

    def post(self):
        jsonData = request.form.to_dict()
        return self.service.saveRecord(jsonData, request.files)


class ReqStepApprovalHandlerController(Resource):
    service = GenericServices(
        Model=RequestStepApproval,
        Schema=RequestStepApprovalSchema
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
