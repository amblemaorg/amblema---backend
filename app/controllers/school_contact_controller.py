# /app/controllers/school_contact_controller.py


from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.services.school_contact_service import SchoolContactService
from app.models.school_contact_model import SchoolContact
from app.schemas.school_contact_schema import SchoolContactSchema
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class SchoolContactController(Resource):

    service = GenericServices(
        Model=SchoolContact,
        Schema=SchoolContactSchema)

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    @jwt_required
    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class SchoolContactHandlerController(Resource):

    service = SchoolContactService(
        Model=SchoolContact,
        Schema=SchoolContactSchema)

    @jwt_required
    def get(self, id):
        return self.service.getRecord(id)

    @jwt_required
    def put(self, id):
        jsonData = request.get_json()
        return self.service.updateRecord(
            recordId=id,
            jsonData=jsonData,
            partial=True)

    @jwt_required
    def delete(self, id):
        return self.service.deleteRecord(id)
