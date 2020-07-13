# app/controllers/amblecoin_controller.py


from flask import request
from flask_restful import Resource

from app.services.amblecoin_service import AmbleCoinService
from app.helpers.handler_authorization import jwt_required


class AmbleCoinController(Resource):

    service = AmbleCoinService()

    @jwt_required
    def post(self, lapse):
        jsonData = request.form.to_dict()
        return self.service.save(lapse, jsonData, request.files)

    @jwt_required
    def get(self, lapse):
        return self.service.get(lapse)
