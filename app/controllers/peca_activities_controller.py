# app/controllers/peca_activities_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_activities_service import ActivitiesPecaService, CronPecaActivitiesService, ReportActivityService
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

class CronPecaActivitiesCtrl(Resource):
    service = CronPecaActivitiesService()
    def get(self, limit, skip):
        return self.service.cronPecaActivities(limit, skip)

class ReportActivitiesCtrl(Resource):
    service = ReportActivityService()
    def get(self):
        return self.service.getDataInicial()