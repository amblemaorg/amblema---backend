# app/controllers/peca_initial_workshop_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_initial_workshop_service import InitialWorkshopService
from app.helpers.handler_authorization import jwt_required


class PecaInitialWorkshopCtrl(Resource):

    service = InitialWorkshopService()

    @jwt_required
    def get(self, pecaId, lapse):
        return self.service.get(pecaId, lapse)

    @jwt_required
    def post(self, pecaId, lapse):
        userId = request.args.get('userId')
        jsonData = request.get_json()
        return self.service.save(pecaId, lapse, jsonData, userId, None)
