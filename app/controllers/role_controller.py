# /app/controllers/role_controller.py


from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.services.role_service import RoleService
from app.models.role_model import Role
from app.schemas.role_schema import RoleSchema
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class RoleController(Resource):
    service = RoleService(
        Model=Role,
        Schema=RoleSchema)

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    @jwt_required
    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class RoleHandlerController(Resource):
    service = RoleService(
        Model=Role,
        Schema=RoleSchema
    )

    @jwt_required
    def get(self, roleId):
        return self.service.getRecord(roleId)

    @jwt_required
    def put(self, roleId):
        jsonData = request.get_json()
        return self.service.updateRecord(
            recordId=roleId,
            jsonData=jsonData,
            partial=True)

    @jwt_required
    def delete(self, roleId):
        return self.service.deleteRecord(roleId)
