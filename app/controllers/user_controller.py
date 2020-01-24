# /app/views/municipality.py


from flask import request
from flask_restful import Resource

from app.models.user_model import (
    User,
    AdministratorUser,
    CoordinatorUser,
    SponsorUser,
    SchoolUser,
    UserSchema,
    AdminUserSchema,
    CoordinatorUserSchema,
    SponsorUserSchema,
    SchoolUserSchema
)
from app.services.generic_service import GenericServices
from app.helpers.handler_request import getQueryParams

class UserController(Resource):

    def get(self):
        filters = getQueryParams(request)
        service = getService(request)
        return service.getAllRecords(filters=filters)

    def post(self):
        
        jsonData = request.get_json()
        service = getService(request)
        return service.saveRecord(jsonData)

    
class UserHandlerController(Resource):

    def get(self, userId):
        service = getService(request)
        return service.getRecord(userId)
    
    def put(self, userId):
        jsonData = request.get_json()
        service = getService(request)
        return service.updateRecord(
            recordId=userId,
            jsonData=jsonData,
            partial=(True),
            exclude=("password",))

    def delete(self, userId):
        service = getService(request)
        return service.deleteRecord(userId)


def getService(request):
    service = GenericServices(
        Model=User,
        Schema=UserSchema
    )
    if 'userType' in request.args:
        if str(request.args['userType']) == '1':
            service.Model = AdministratorUser
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