# /app/controllers/state_controller.py


from flask import request
from flask_restful import Resource

from app.services.state_service import StateService
from app.models.state_model import State, StateSchema
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class StateController(Resource):

    service = StateService(
        Model=State,
        Schema=StateSchema)

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    @jwt_required
    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class StateHandlerController(Resource):

    service = StateService(
        Model=State,
        Schema=StateSchema)

    def get(self, stateId):
        return self.service.getRecord(stateId)

    @jwt_required
    def put(self, stateId):
        jsonData = request.get_json()
        return self.service.updateRecord(
            recordId=stateId,
            jsonData=jsonData,
            partial=("name",))

    @jwt_required
    def delete(self, stateId):
        return self.service.deleteRecord(stateId)
