# app/controllers/environmental_project_controller.py


from flask import request
from flask_restful import Resource

from app.services.environmental_project_service import EnvironmentalProjectService
from app.helpers.handler_authorization import jwt_required


class EnvironmentalProjectController(Resource):

    service = EnvironmentalProjectService()

    @jwt_required
    def post(self):
        jsonData = request.get_json()
        return self.service.save(jsonData)

    @jwt_required
    def get(self):
        return self.service.get()
