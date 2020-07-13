# app/controllers/peca_activities_slider_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_activities_slider_service import ActivitiesSliderService
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class ActivitiesSliderController(Resource):

    service = ActivitiesSliderService()

    @jwt_required
    def put(self, pecaId):
        userId = request.args.get('userId')
        jsonData = request.get_json()
        return self.service.save(pecaId, userId, jsonData)
