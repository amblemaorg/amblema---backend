# app/controllers/lapse_planning_controller.py


from flask import request
from flask_restful import Resource

from app.services.lapse_planning_service import LapsePlanningService


class LapsePlanningController(Resource):

    service = LapsePlanningService()

    def post(self, lapse):
        jsonData = request.form.to_dict()
        return self.service.save(jsonData, lapse, request.files)

    def get(self, lapse):
        return self.service.get(lapse)
