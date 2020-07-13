# /app/controllers/coordiator_contact_controller.py


from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.services.coordinator_contact_service import CoordinatorContactService
from app.models.coordinator_contact_model import CoordinatorContact
from app.schemas.coordinator_contact_schema import CoordinatorContactSchema
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class CoordinatorContactController(Resource):

    service = GenericServices(
        Model=CoordinatorContact,
        Schema=CoordinatorContactSchema)

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    @jwt_required
    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class CoordinatorContactHandlerController(Resource):

    service = CoordinatorContactService(
        Model=CoordinatorContact,
        Schema=CoordinatorContactSchema)

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
