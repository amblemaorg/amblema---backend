# app/controllers/peca_amblecoins_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_amblecoins_service import AmblecoinsPecaService
from app.helpers.handler_authorization import jwt_required


class PecaAmblecoinsController(Resource):

    service = AmblecoinsPecaService()

    @jwt_required
    def get(self, pecaId, lapse):
        return self.service.get(pecaId, lapse)

    @jwt_required
    def put(self, pecaId, lapse):
        jsonData = request.get_json()
        return self.service.save(pecaId, lapse, jsonData)

class PecaAmbleSectionCtrl(Resource):
    service = AmblecoinsPecaService()
    @jwt_required
    def put(self, pecaId, lapse):
        jsonData = request.get_json()
        return self.service.updateSection(pecaId, lapse, jsonData)
