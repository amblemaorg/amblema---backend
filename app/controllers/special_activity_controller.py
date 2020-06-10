# /app/controllers/special_activity_controller.py


from flask import request
from flask_restful import Resource

from app.services.special_activity_service import SpecialActivityService
from app.helpers.handler_request import getQueryParams


class SpecialActivityController(Resource):

    service = SpecialActivityService()

    def post(self, pecaId, lapse):
        userId = request.args.get('userId')
        jsonData = request.get_json()
        print(pecaId)
        print(lapse)
        print(jsonData)
        return self.service.save(pecaId, lapse, userId, jsonData)