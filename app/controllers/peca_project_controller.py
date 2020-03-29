# app/controllers/peca_project_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_project_service import PecaProjectService
from app.helpers.handler_request import getQueryParams


class PecaProjectController(Resource):

    service = PecaProjectService()

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAll(filters=filters)


class PecaProjectHandlerController(Resource):

    service = PecaProjectService()

    def get(self, id):
        return self.service.get(id=id)


class SchoolController(Resource):
    service = PecaProjectService()

    def get(self, id):
        return self.service.getSchool(id)

    def put(self, id):
        jsonData = request.get_json()
        return self.service.updateSchool(id, jsonData)
