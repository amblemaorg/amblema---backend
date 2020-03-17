# /app/controllers/state_controller.py


from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.state_model import State, StateSchema
from app.helpers.handler_request import getQueryParams


class StateController(Resource):
    
    service = GenericServices(
        Model=State,
        Schema=StateSchema)

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)

    
class StateHandlerController(Resource):
    
    service = GenericServices(
        Model=State,
        Schema=StateSchema)

    def get(self, stateId):
        return self.service.getRecord(stateId)
    
    def put(self, stateId):
        jsonData = request.get_json()
        return self.service.updateRecord(
            recordId=stateId,
            jsonData=jsonData,
            partial=("name",))

    def delete(self, stateId):
        return self.service.deleteRecord(stateId)