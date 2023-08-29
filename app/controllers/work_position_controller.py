# /app/controllers/work_position_controller.py


from flask import request
from flask_restful import Resource

from app.services.work_position_service import WorkPositionService
from app.models.work_position_model import WorkPosition
from app.schemas.work_position_schema import WorkPositionSchema
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class WorkPositionController(Resource):

    service = WorkPositionService(
        Model=WorkPosition,
        Schema=WorkPositionSchema)

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    @jwt_required
    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class WorkPositionHandlerController(Resource):

    service = WorkPositionService(
        Model=WorkPosition,
        Schema=WorkPositionSchema)

    def get(self, workPositionId):
        return self.service.getRecord(workPositionId)

    @jwt_required
    def put(self, workPositionId):
        jsonData = request.get_json()
        return self.service.updateRecord(
            recordId=workPositionId,
            jsonData=jsonData,
            partial=("name",))

    @jwt_required
    def delete(self, workPositionId):
        return self.service.deleteRecord(workPositionId)
