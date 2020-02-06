# /app/controllers/state_controller.py


from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.steps_traking_model import StepsTracking, StepsTrackingSchema
from app.helpers.handler_request import getQueryParams


class StepsTrackingController(Resource):
    
    service = GenericServices(
        Model=StepsTracking,
        Schema=StepsTrackingSchema)

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    
class StepsTrackingHandlerController(Resource):
    
    service = GenericServices(
        Model=StepsTracking,
        Schema=StepsTrackingSchema)

    def get(self, id):
        return self.service.getRecord(id)
    
    def put(self, id):
        jsonData = request.form.to_dict()
        return self.service.updateRecord(
            recordId=id,
            jsonData=jsonData,
            files=request.files,
            partial=True)

    def delete(self, id):
        return self.service.deleteRecord(id)