# /app/controllers/activity_controller.py


from flask import request
from flask_restful import Resource

from app.services.activity_service import ActivityService, Activity, ActivitySchema
from app.services.amblecoin_service import AmbleCoinService
from app.services.initial_workshop_service import InicialWorkshopService
from app.services.lapse_planning_service import LapsePlanningService
from app.services.annual_convention_service import AnnualConventionService
from app.helpers.handler_request import getQueryParams


class ActivityController(Resource):

    service = ActivityService()

    def post(self, lapse):
        jsonData = request.form.to_dict()
        return self.service.save(lapse, jsonData, request.files)


class ActivityHandlerController(Resource):

    service = ActivityService()
    standards = {
        'initialworkshop': InicialWorkshopService(),
        'lapseplanning': LapsePlanningService(),
        'amblecoins': AmbleCoinService(),
        'annualconvention': AnnualConventionService()
    }

    def get(self, id, lapse):

        if id in self.standards:
            return self.standards[id].get(lapse)
        return self.service.get(lapse, id)

    def put(self, id, lapse):
        jsonData = request.form.to_dict()
        if id in self.standards:
            return self.standards[id].save(lapse=lapse, jsonData=jsonData, files=request.files)
        return self.service.update(
            lapse=lapse,
            id=id,
            jsonData=jsonData,
            files=request.files)

    def delete(self, id, lapse):
        return self.service.delete(lapse, id)


class ActivitySummaryController(Resource):
    service = ActivityService()

    def get(self):
        filters = None
        if 'status' in request.args:
            filters = {'status': request.args['status']}

        return self.service.getSumary(filters=filters)

    def post(self):
        jsonData = request.get_json()
        return self.service.handleEnable(jsonData)
