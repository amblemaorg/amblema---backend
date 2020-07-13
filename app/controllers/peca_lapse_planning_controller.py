# app/controllers/peca_lapse_planning_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_lapse_planning_service import LapsePlanningService
from app.helpers.handler_authorization import jwt_required


class PecaLapsePlanningCtrl(Resource):

    service = LapsePlanningService()

    @jwt_required
    def get(self, pecaId, lapse):
        return self.service.get(pecaId, lapse)

    @jwt_required
    def post(self, pecaId, lapse):
        jsonData = request.form.to_dict()
        userId = request.args.get('userId')
        return self.service.save(pecaId, lapse, jsonData, userId, request.files)
