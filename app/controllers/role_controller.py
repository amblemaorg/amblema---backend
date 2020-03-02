# /app/controllers/role_controller.py


from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.services.role_service import EntityService, RoleService
from app.models.role_model import (
    Entity,
    EntitySchema,
    Role,
    RoleSchema)
from app.helpers.handler_request import getQueryParams


class EntityController(Resource):

    service = EntityService(
        Model=Entity,
        Schema=EntitySchema)

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class EntityHandlerController(Resource):

    service = EntityService(
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


class RoleController(Resource):
    service = RoleService(
        Model=Role,
        Schema=RoleSchema)

    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters, exclude=("permissions",))

    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class RoleHandlerController(Resource):
    service = GenericServices(
        Model=Role,
        Schema=RoleSchema
    )

    def get(self, roleId):
        return self.service.getRecord(roleId)

    def put(self, roleId):
        jsonData = request.get_json()
        return self.service.updateRecord(
            recordId=roleId,
            jsonData=jsonData,
            partial=True)

    def delete(self, roleId):
        return self.service.deleteRecord(roleId)
