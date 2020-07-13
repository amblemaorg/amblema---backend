# app/controllers/request_find_all_controller.py


from flask import request, current_app
from flask_restful import Resource

from app.services.request_all_service import RequestsAll
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class ReqContactAllController(Resource):
    service = RequestsAll()

    @jwt_required
    def get(self):
        return self.service.getAllContactsRequest()


class ReqFindAllController(Resource):
    service = RequestsAll()

    @jwt_required
    def get(self):
        return self.service.getAllFindRequest()
