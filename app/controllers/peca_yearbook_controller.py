# app/controllers/peca_yearbook_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_yearbook_service import YearbookService
from app.helpers.handler_authorization import jwt_required


class PecaYearbookController(Resource):

    service = YearbookService()

    #@jwt_required
    def post(self, pecaId):
        jsonData = request.get_json()
        userId = request.args.get('userId')
        return self.service.save(pecaId, userId, jsonData)
