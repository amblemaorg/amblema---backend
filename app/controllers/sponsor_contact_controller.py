# /app/controllers/sponsor_contact_controller.py


from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.services.sponsor_contact_service import SponsorContactService
from app.models.sponsor_contact_model import SponsorContact
from app.schemas.sponsor_contact_schema import SponsorContactSchema
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class SponsorContactController(Resource):

    service = GenericServices(
        Model=SponsorContact,
        Schema=SponsorContactSchema)

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        return self.service.getAllRecords(filters=filters)

    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class SponsorContactHandlerController(Resource):

    service = SponsorContactService(
        Model=SponsorContact,
        Schema=SponsorContactSchema)

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
