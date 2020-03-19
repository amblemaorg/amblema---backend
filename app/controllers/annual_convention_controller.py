# app/controllers/annual_convention_controller.py


from flask import request
from flask_restful import Resource

from app.services.annual_convention_service import AnnualConventionService


class AnnualConventionController(Resource):

    service = AnnualConventionService()

    def post(self):

        jsonData = request.form.to_dict()
        return self.service.save(jsonData, request.files)

    def get(self):
        return self.service.get()
