# app/controllers/peca_schedule_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_schedule_service import ScheduleService
from app.helpers.handler_authorization import jwt_required


class ScheduleController(Resource):

    service = ScheduleService()

    @jwt_required
    def get(self, pecaId):
        return self.service.getSchedule(pecaId)

    @jwt_required
    def post(self, pecaId):
        jsonData = request.get_json()
        return self.service.save(pecaId, jsonData)
