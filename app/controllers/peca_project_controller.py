# app/controllers/peca_project_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_project_service import PecaProjectService
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class PecaProjectController(Resource):

    service = PecaProjectService()

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        return self.service.getAll(filters=filters)


class PecaProjectHandlerController(Resource):

    service = PecaProjectService()

    @jwt_required
    def get(self, id):
        return self.service.get(id=id)
