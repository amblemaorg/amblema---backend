# /app/controllers/learning_module_controller.py


from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.learning_module_model import LearningModule
from app.schemas.learning_module_schema import LearningModuleSchema
from app.helpers.handler_request import getQueryParams
from app.services.coordinator_service import CoordinatorService
from app.helpers.handler_authorization import jwt_required


class LearningController(Resource):

    service = GenericServices(
        Model=LearningModule,
        Schema=LearningModuleSchema)

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    @jwt_required
    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class LearningHandlerController(Resource):

    service = GenericServices(
        Model=LearningModule,
        Schema=LearningModuleSchema)

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


class AnswerLearningModuleController(Resource):
    service = CoordinatorService()

    @jwt_required
    def post(self, id):
        jsonData = request.get_json()
        return self.service.tryAnswerModule(id, jsonData)
