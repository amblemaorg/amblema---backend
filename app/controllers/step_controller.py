# /app/controllers/step_controller.py


from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.step_model import Step
from app.schemas.step_schema import StepSchema
from app.helpers.handler_request import getQueryParams


class StepController(Resource):

    service = GenericServices(
        Model=Step,
        Schema=StepSchema)

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    def post(self):
        jsonData = request.form.to_dict()
        return self.service.saveRecord(jsonData, request.files)


class StepHandlerController(Resource):

    service = GenericServices(
        Model=Step,
        Schema=StepSchema)

    def get(self, id):
        return self.service.getRecord(id)

    def put(self, id):
        jsonData = request.form.to_dict()
        return self.service.updateRecord(
            recordId=id,
            jsonData=jsonData,
            files=request.files,
            partial=["name", "tag", "text", "date", "file", "schoolYear"])

    def delete(self, id):
        return self.service.deleteRecord(id)
