# /app/controllers/activity_controller.py


from flask import request
from flask_restful import Resource

from app.services.activity_service import ActivityService, Activity, ActivitySchema
from app.helpers.handler_request import getQueryParams


class ActivityController(Resource):

    service = ActivityService()

    def post(self, lapse):
        jsonData = request.form.to_dict()
        return self.service.save(lapse, jsonData, request.files)


class ActivityHandlerController(Resource):

    service = ActivityService()

    def get(self, lapse, id):
        return self.service.get(lapse, id)

    def put(self, lapse, id):
        jsonData = request.form.to_dict()
        return self.service.update(
            lapse=lapse,
            id=id,
            jsonData=jsonData,
            files=request.files)

    def delete(self, lapse, id):
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
