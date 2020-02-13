# /app/controllers/learning_module_controller.py


from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.learning_module_model import LearningModule
from app.schemas.learning_module_schema import LearningModuleSchema
from app.helpers.handler_request import getQueryParams


class LearningController(Resource):

    service = GenericServices(
        Model=LearningModule,
        Schema=LearningModuleSchema)

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class LearningHandlerController(Resource):

    service = GenericServices(
        Model=LearningModule,
        Schema=LearningModuleSchema)

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
