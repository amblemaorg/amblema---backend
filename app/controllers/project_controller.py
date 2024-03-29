# /app/controllers/project_controller.py


from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.services.project_service import ProjectService
from app.services.project_handler_service import ProjectHandlerService
from app.models.project_model import Project
from app.schemas.project_schema import ProjectSchema
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class ProjectController(Resource):

    service = GenericServices(
        Model=Project,
        Schema=ProjectSchema)

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(
            filters=filters,
            exclude=(
                "stepsProgress",
            ))

    @jwt_required
    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class ProjectHandlerController(Resource):

    service = ProjectHandlerService(
        Model=Project,
        Schema=ProjectSchema)

    @jwt_required
    def get(self, id):
        return self.service.getRecord(id)

    @jwt_required
    def put(self, id):
        jsonData = request.get_json()
        print(jsonData)
        return self.service.updateRecord(
            recordId=id,
            jsonData=jsonData,
            files=request.files,
            partial=True)

    @jwt_required
    def delete(self, id):
        return self.service.deleteRecord(id)


class ProjectStepsController(Resource):
    service = ProjectService()

    @jwt_required
    def post(self, id):
        jsonData = request.form.to_dict()
        return self.service.updateStep(id, jsonData, request.files)


class ProjectPecaController(Resource):
    service = ProjectService()

    @jwt_required
    def get(self, id):
        """
        create a peca for a project  
        params : id -> projectId
        """

        return self.service.handlerCreatePeca(id)
