# app/controllers/annual_convention_controller.py


from flask import request
from flask_restful import Resource

from app.services.annual_convention_service import AnnualConventionService
from app.helpers.handler_authorization import jwt_required


class AnnualConventionController(Resource):

    service = AnnualConventionService()

    @jwt_required
    def post(self, lapse):

        jsonData = request.form.to_dict()
        return self.service.save(lapse, jsonData)

    @jwt_required
    def get(self, lapse):
        return self.service.get(lapse)
