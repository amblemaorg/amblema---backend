# app/controllers/monitoring_activities_controller.py


from flask import request
from flask_restful import Resource

from app.services.monitoring_activities_service import MonitoringActivitiesService


class MonitoringActivitiesController(Resource):

    service = MonitoringActivitiesService()

    def post(self):
        jsonData = request.get_json()
        return self.service.save(jsonData)

    def get(self):
        return self.service.get()
