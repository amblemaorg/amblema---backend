# /app/views/municipality.py


from flask import request
from flask_restful import Resource

from app.services.municipality_service import (
    getAllMunicipalities,
    saveMunicipality,
    getMunicipality,
    updateMunicipality,
    deleteMunicipality)


class MunicipalityController(Resource):
    def get(self, stateId):
        return getAllMunicipalities(stateId)

    def post(self, stateId):
        jsonData = request.get_json()
        return saveMunicipality(stateId, jsonData)

    
class MunicipalityHandlerController(Resource):
    def get(self, stateId, municipalityId):
        return getMunicipality(stateId, municipalityId)
    
    def put(self, stateId, municipalityId):
        jsonData = request.get_json()
        return updateMunicipality(stateId, municipalityId, jsonData)

    def delete(self, stateId, municipalityId):
        return deleteMunicipality(stateId, municipalityId)