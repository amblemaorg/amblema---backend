# app/controllers/annual_convention_controller.py


from flask import request
from flask_restful import Resource

from app.services.annual_preparation_service import AnnualPreparationService


class AnnualPreparationController(Resource):

    service = AnnualPreparationService()

    def post(self, lapse):

        jsonData = request.form.to_dict()
        return self.service.save(lapse, jsonData, request.files)

    def get(self, lapse):
        return self.service.get(lapse)
