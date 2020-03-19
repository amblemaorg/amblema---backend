# /app/controllers/entity_controller.py


from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.entity_model import Entity
from app.schemas.entity_schema import EntitySchema
from app.helpers.handler_request import getQueryParams


class EntityController(Resource):

    service = GenericServices(
        Model=Entity,
        Schema=EntitySchema)

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class EntityHandlerController(Resource):

    service = GenericServices(
        Model=Entity,
        Schema=EntitySchema)

    def get(self, entityId):
        return self.service.getRecord(entityId)

    def put(self, entityId):
        jsonData = request.get_json()
        return self.service.updateRecord(
            recordId=entityId,
            jsonData=jsonData,
            partial=True)

    def delete(self, entityId):
        return self.service.deleteRecord(entityId)
