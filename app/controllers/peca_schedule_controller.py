# app/controllers/peca_schedule_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_schedule_service import ScheduleService


class ScheduleController(Resource):

    service = ScheduleService()

    def get(self, pecaId):
        return self.service.getSchedule(pecaId)

    def post(self, pecaId):
        jsonData = request.get_json()
        return self.service.save(pecaId, jsonData)
