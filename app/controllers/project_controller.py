# /app/controllers/project_controller.py


from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.services.project_service import ProjectService
from app.models.project_model import Project
from app.schemas.project_schema import ProjectSchema
from app.helpers.handler_request import getQueryParams


class ProjectController(Resource):

    service = GenericServices(
        Model=Project,
        Schema=ProjectSchema)

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(
            filters=filters,
            exclude=(
                "stepsProgress",
            ))

    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class ProjectHandlerController(Resource):

    service = GenericServices(
        Model=Project,
        Schema=ProjectSchema)

    def get(self, id):
        return self.service.getRecord(id)

    def put(self, id):
        jsonData = request.get_json()
        return self.service.updateRecord(
            recordId=id,
            jsonData=jsonData,
            files=request.files,
            partial=True)

    def delete(self, id):
        return self.service.deleteRecord(id)


class ProjectStepsController(Resource):
    service = ProjectService()

    def post(self, id):
        jsonData = request.form.to_dict()
        return self.service.updateStep(id, jsonData, request.files)


class ProjectPecaController(Resource):
    service = ProjectService()

    def get(self, id):
        """
        create a peca for a project  
        params : id -> projectId
        """

        return self.service.handlerCreatePeca(id)
