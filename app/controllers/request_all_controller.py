# app/controllers/request_find_all_controller.py


from flask import request, current_app
from flask_restful import Resource

from app.services.request_all_service import RequestsAll
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required
from app.helpers.school_year_filter import get_school_year_date_filters


class ReqContactAllController(Resource):
    service = RequestsAll()

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        if not filters:
            filters = []
        filters.extend(get_school_year_date_filters())
        
        only = None
        if 'only' in request.args:
            only = request.args['only'].split(',')
        return self.service.getAllContactsRequest(filters=filters, only=only)


class ReqFindAllController(Resource):
    service = RequestsAll()

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        if not filters:
            filters = []
        filters.extend(get_school_year_date_filters())
        
        only = None
        if 'only' in request.args:
            only = request.args['only'].split(',')
        return self.service.getAllFindRequest(filters=filters, only=only)
