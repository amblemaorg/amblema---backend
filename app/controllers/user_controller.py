# /app/views/municipality.py


from flask import request
from flask_restful import Resource

from app.models.user_model import User
from app.models.admin_user_model import AdminUser
from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.coordinator_user_model import CoordinatorUser
from app.schemas.user_schema import UserSchema
from app.schemas.admin_user_schema import AdminUserSchema
from app.schemas.school_user_schema import SchoolUserSchema
from app.schemas.sponsor_user_schema import SponsorUserSchema
from app.schemas.coordinator_user_schema import CoordinatorUserSchema
from app.services.user_service import (UserService, ResendEmailCoordinator)
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class UserController(Resource):

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        service = getService(request)
        return service.getAllRecords(filters=filters)

    @jwt_required
    def post(self):
        jsonData = request.get_json()
        service = getService(request)
        return service.saveRecord(jsonData)


class UserHandlerController(Resource):

    @jwt_required
    def get(self, userId):
        service = getService(request)
        return service.getRecord(userId)

    @jwt_required
    def put(self, userId):
        jsonData = request.get_json()
        service = getService(request)
        return service.updateRecord(
            recordId=userId,
            jsonData=jsonData,
            partial=(True))

    @jwt_required
    def delete(self, userId):
        service = getService(request)
        return service.deleteRecord(userId)


def getService(request):
    service = UserService(
        Model=User,
        Schema=UserSchema
    )
    if 'userType' in request.args:
        if str(request.args['userType']) == '1':
            service.Model = AdminUser
            service.Schema = AdminUserSchema
        elif str(request.args['userType']) == '2':
            service.Model = CoordinatorUser
            service.Schema = CoordinatorUserSchema
        elif str(request.args['userType']) == '3':
            service.Model = SponsorUser
            service.Schema = SponsorUserSchema
        elif str(request.args['userType']) == '4':
            service.Model = SchoolUser
            service.Schema = SchoolUserSchema
    return service

class ResendEmailCoordinatorController(Resource):
    def post(self, id):
        service = ResendEmailCoordinator()
        return service.post(id)

        