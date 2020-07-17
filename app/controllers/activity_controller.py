# /app/controllers/activity_controller.py


from flask import request
from flask_restful import Resource
from app.helpers.handler_authorization import (jwt_required)

from app.services.activity_service import ActivityService, Activity, ActivitySchema
from app.services.amblecoin_service import AmbleCoinService
from app.services.initial_workshop_service import InicialWorkshopService
from app.services.lapse_planning_service import LapsePlanningService
from app.services.annual_preparation_service import AnnualPreparationService
from app.services.annual_convention_service import AnnualConventionService
from app.services.math_olympic_service import MathOlympicService
from app.services.special_lapse_activity_service import SpecialLapseActivityService
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class ActivityController(Resource):

    service = ActivityService()

    @jwt_required
    def post(self, lapse):
        jsonData = request.form.to_dict()
        return self.service.save(lapse, jsonData, request.files)


class ActivityHandlerController(Resource):

    service = ActivityService()
    standards = {
        'initialworkshop': InicialWorkshopService(),
        'lapseplanning': LapsePlanningService(),
        'amblecoins': AmbleCoinService(),
        'annualpreparation': AnnualPreparationService(),
        'annualconvention': AnnualConventionService(),
        'matholympic': MathOlympicService(),
        'speciallapseactivity': SpecialLapseActivityService()
    }

    @jwt_required
    def get(self, id, lapse):

        if id in self.standards:
            return self.standards[id].get(lapse)
        return self.service.get(lapse, id)

    @jwt_required
    def put(self, id, lapse):
        jsonData = request.form.to_dict()
        if id in self.standards:
            return self.standards[id].save(lapse=lapse, jsonData=jsonData, files=request.files)
        return self.service.update(
            lapse=lapse,
            id=id,
            jsonData=jsonData,
            files=request.files)

    @jwt_required
    def delete(self, id, lapse):
        return self.service.delete(lapse, id)


class ActivitySummaryController(Resource):
    service = ActivityService()

    @jwt_required
    def get(self):
        filters = None
        if 'status' in request.args:
            filters = {'status': request.args['status']}

        return self.service.getSumary(filters=filters)

    @jwt_required
    def post(self):
        jsonData = request.get_json()
        return self.service.handleEnable(jsonData)
