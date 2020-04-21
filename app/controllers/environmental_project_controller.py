# app/controllers/environmental_project_controller.py


from flask import request
from flask_restful import Resource

from app.services.environmental_project_service import EnvironmentalProjectService


class EnvironmentalProjectController(Resource):

    service = EnvironmentalProjectService()

    def post(self):
        jsonData = request.get_json()
        return self.service.save(jsonData)

    def get(self):
        return self.service.get()
