# -*- coding: utf-8 -*-
# app/controllers/vademecum/access_controller.py
"""Solicitudes de acceso (pública y backoffice) y autorizaciones por año (API-05)."""

from flask import g, request
from flask_restful import Resource

from app.helpers.vademecum_auth import vademecum_admin_required
from app.services.vademecum.access_request_service import AccessRequestService, with_record


class AccessRequestController(Resource):
    def post(self):
        return AccessRequestService().create(request.get_json(silent=True))


class AdminAccessRequestListController(Resource):
    @vademecum_admin_required
    def get(self):
        return AccessRequestService().list(request.args)


class AdminAccessRequestApproveController(Resource):
    @vademecum_admin_required
    def post(self, requestId):
        service = AccessRequestService()
        return with_record(service.get(requestId),
                           lambda r: service.approve(r, g.vademecum_admin))


class AdminAccessRequestRejectController(Resource):
    @vademecum_admin_required
    def post(self, requestId):
        service = AccessRequestService()
        data = request.get_json(silent=True)
        return with_record(service.get(requestId),
                           lambda r: service.reject(r, data, g.vademecum_admin))


class AdminAuthorizationListController(Resource):
    @vademecum_admin_required
    def get(self):
        return AccessRequestService().list_authorizations(request.args)


class AdminAuthorizationRevokeController(Resource):
    @vademecum_admin_required
    def post(self, authorizationId):
        service = AccessRequestService()
        return with_record(service.get_authorization(authorizationId), service.revoke)
