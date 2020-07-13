# app/controllers/request_step_approval_controller.py


from flask import request, current_app
from flask_restful import Resource

from app.services.steps_approval_service import StepsApprovalService
from app.models.request_step_approval_model import RequestStepApproval
from app.schemas.request_step_approval_schema import RequestStepApprovalSchema
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class ReqStepApprovalController(Resource):
    service = StepsApprovalService(
        Model=RequestStepApproval,
        Schema=RequestStepApprovalSchema
    )

    @jwt_required
    def post(self):
        jsonData = request.form.to_dict()
        return self.service.saveRecord(jsonData, request.files)
