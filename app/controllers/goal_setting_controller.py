# app/controllers/goal_setting_controller.py


from flask import request
from flask_restful import Resource

from app.services.goal_setting_service import GoalSettingService
from app.helpers.handler_authorization import jwt_required


class GoalSettingController(Resource):

    service = GoalSettingService()

    @jwt_required
    def post(self):
        jsonData = request.get_json()
        return self.service.save(jsonData)

    @jwt_required
    def get(self, schoolYearId=None):
        return self.service.get(schoolYearId)
