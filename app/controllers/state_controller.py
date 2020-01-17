# /app/views/state.py


from flask import request
from flask_restful import Resource


from app.services.state_service import (
    getAllStates,
    saveState,
    getState,
    updateState,
    deleteState)

class StateController(Resource):
    def get(self):
        return getAllStates()

    def post(self):
        jsonData = request.get_json()
        return saveState(jsonData)

    
class StateHandlerController(Resource):
    def get(self, stateId):
        return getState(stateId)
    
    def put(self, stateId):
        jsonData = request.get_json()
        return updateState(stateId,jsonData)

    def delete(self, stateId):
        return deleteState(stateId)