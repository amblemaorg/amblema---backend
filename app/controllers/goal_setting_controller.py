# app/controllers/goal_setting_controller.py


from flask import request
from flask_restful import Resource

from app.services.goal_setting_service import GoalSettingService


class GoalSettingController(Resource):

    service = GoalSettingService()

    def post(self):

        jsonData = request.get_json()
        return self.service.save(jsonData)

    def get(self, schoolYearId=None):
        return self.service.get(schoolYearId)
