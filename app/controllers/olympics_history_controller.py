# app/controllers/olympics_history_controller.py

from flask import request
from flask_restful import Resource
from app.services.olympics_history_service import OlympicsHistoryService
from app.models.olympics_history_model import OlympicsHistory
from app.schemas.olympics_history_schema import OlympicsHistorySchema

class OlympicsHistoryController(Resource):
    service = OlympicsHistoryService(
        Model=OlympicsHistory,
        Schema=OlympicsHistorySchema
    )

    def get(self):
        return self.service.getRecord()

    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)
