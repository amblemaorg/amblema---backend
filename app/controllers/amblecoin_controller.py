# app/controllers/amblecoin_controller.py


from flask import request
from flask_restful import Resource

from app.services.amblecoin_service import AmbleCoinService


class AmbleCoinController(Resource):

    service = AmbleCoinService()

    def post(self):

        jsonData = request.form.to_dict()
        return self.service.save(jsonData, request.files)

    def get(self):
        return self.service.get()
