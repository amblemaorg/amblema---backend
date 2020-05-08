# app/controllers/peca_amblecoins_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_amblecoins_service import AmblecoinsPecaService


class PecaAmblecoinsController(Resource):

    service = AmblecoinsPecaService()

    def get(self, pecaId, lapse):
        return self.service.get(pecaId, lapse)

    def put(self, pecaId, lapse):
        jsonData = request.get_json()
        return self.service.save(pecaId, lapse, jsonData)

