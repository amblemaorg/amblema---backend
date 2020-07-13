# /app/controllers/step_controller.py


from flask import request
from flask_restful import Resource
from flask import current_app

from app.services.step_handler_service import StepHandlerService
from app.models.step_model import Step
from app.schemas.step_schema import StepSchema
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class StepController(Resource):

    service = StepHandlerService(
        Model=Step,
        Schema=StepSchema)

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    @jwt_required
    def post(self):
        jsonData = request.form.to_dict()
        return self.service.saveRecord(jsonData, request.files)


class StepHandlerController(Resource):

    service = StepHandlerService(
        Model=Step,
        Schema=StepSchema)

    @jwt_required
    def get(self, id):
        return self.service.getRecord(id)

    @jwt_required
    def put(self, id):
        jsonData = request.form.to_dict()
        return self.service.updateRecord(
            recordId=id,
            jsonData=jsonData,
            files=request.files,
            partial=True)

    @jwt_required
    def delete(self, id):
        return self.service.deleteRecord(id)
