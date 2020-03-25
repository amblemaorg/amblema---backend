# app/controllers/request_find_all_controller.py


from flask import request, current_app
from flask_restful import Resource

from app.services.request_all_service import RequestsAll
from app.helpers.handler_request import getQueryParams


class ReqContactAllController(Resource):
    service = RequestsAll()

    def get(self):
        return self.service.getAllContactsRequest()
