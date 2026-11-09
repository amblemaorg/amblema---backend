# -*- coding: utf-8 -*-
# app/controllers/teacher_coevaluation_controller.py

from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import verify_jwt_in_request_optional, get_jwt_identity

from app.services.teacher_coevaluation_service import TeacherCoevaluationService
from app.helpers.handler_authorization import jwt_required, admin_required, get_current_user


def _caller():
    """
    Usuario del token. En TESTING jwt_required no valida, así que el token es
    opcional: sin cabecera Authorization devuelve None y el servicio no valida acceso.
    """
    if current_app.config.get("TESTING"):
        verify_jwt_in_request_optional()
        if not get_jwt_identity():
            return None
    return get_current_user()


class TeacherCoevaluationListController(Resource):

    service = TeacherCoevaluationService()

    @jwt_required
    def get(self, pecaId):
        return self.service.get_statuses(pecaId, caller=_caller())


class TeacherCoevaluationController(Resource):

    service = TeacherCoevaluationService()

    @jwt_required
    def get(self, pecaId, teacherId):
        return self.service.get_detail(pecaId, teacherId, caller=_caller())


class TeacherCoevaluationCoordinatorController(Resource):

    service = TeacherCoevaluationService()

    @jwt_required
    def post(self, pecaId, teacherId):
        return self.service.save_coordinator(
            pecaId, teacherId, request.get_json(silent=True), caller=_caller())


class TeacherCoevaluationSendController(Resource):

    service = TeacherCoevaluationService()

    @jwt_required
    def post(self, pecaId, teacherId):
        return self.service.send_link(
            pecaId, teacherId, caller=_caller(), origin=request.headers.get('Origin'))


class TeacherCoevaluationPublicController(Resource):
    """Enlace del docente: sin JWT, autenticado solo por el token."""

    service = TeacherCoevaluationService()

    def get(self, token):
        return self.service.get_public(token)

    def post(self, token):
        return self.service.submit_public(token, request.get_json(silent=True))


class TeacherCoevaluationReportController(Resource):

    service = TeacherCoevaluationService()

    @admin_required
    def get(self, schoolYearId):
        return self.service.report(
            schoolYearId,
            schoolId=request.args.get('schoolId') or None,
            level=request.args.get('level') or None)
