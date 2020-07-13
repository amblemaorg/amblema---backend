# /app/controllers/entity_controller.py


from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.entity_model import Entity
from app.schemas.entity_schema import EntitySchema
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class EntityController(Resource):

    service = GenericServices(
        Model=Entity,
        Schema=EntitySchema)

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    @jwt_required
    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class EntityHandlerController(Resource):

    service = GenericServices(
        Model=Entity,
        Schema=EntitySchema)

    @jwt_required
    def get(self, entityId):
        return self.service.getRecord(entityId)

    @jwt_required
    def put(self, entityId):
        jsonData = request.get_json()
        return self.service.updateRecord(
            recordId=entityId,
            jsonData=jsonData,
            partial=True)

    @jwt_required
    def delete(self, entityId):
        return self.service.deleteRecord(entityId)
