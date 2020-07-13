# app/controllers/peca_activities_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_activities_service import ActivitiesPecaService
from app.helpers.handler_authorization import jwt_required


class PecaActivitiesCtrl(Resource):
    service = ActivitiesPecaService()

    @jwt_required
    def put(self, pecaId, lapse, activityId):
        userId = request.args.get('userId')
        jsonData = request.form.to_dict()
        return self.service.save(pecaId, lapse, activityId, userId, jsonData, request.files)

    @jwt_required
    def get(self, pecaId, lapse, activityId):
        return self.service.get(pecaId, lapse, activityId)
