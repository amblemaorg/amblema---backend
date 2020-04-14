# /app/controllers/role_controller.py


from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.services.role_service import RoleService
from app.models.role_model import Role
from app.schemas.role_schema import RoleSchema
from app.helpers.handler_request import getQueryParams


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
    service = RoleService(
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
