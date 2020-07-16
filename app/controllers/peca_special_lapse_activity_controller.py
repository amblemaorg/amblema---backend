# /app/controllers/peca_special_lapse_activity_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_special_activity_service import PecaSpecialActivityService
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class PecaSpecialActivityController(Resource):

    service = PecaSpecialActivityService()

    @jwt_required
    def post(self, pecaId, lapse):
        userId = request.args.get('userId')
        jsonData = request.get_json()
        return self.service.save(pecaId, lapse, userId, jsonData)

    @jwt_required
    def get(self, pecaId, lapse):
        return self.service.get(pecaId, lapse)

    @jwt_required
    def put(self, pecaId, lapse):
        jsonData = request.get_json()
        return self.service.update(pecaId, lapse, jsonData)

    @jwt_required
    def delete(self, pecaId, lapse):
        return self.service.delete(pecaId, lapse)
