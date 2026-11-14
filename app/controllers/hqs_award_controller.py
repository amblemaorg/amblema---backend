# -*- coding: utf-8 -*-
# app/controllers/hqs_award_controller.py

from flask import request
from flask_restful import Resource

from app.services.hqs_award_service import HqsAwardService
from app.helpers.handler_authorization import admin_required


class HqsAwardReportController(Resource):
    """Reporte de premios Escuela HQS de un año escolar (solo administradores)."""

    service = HqsAwardService()

    @admin_required
    def get(self, schoolYearId):
        return self.service.report(
            schoolYearId,
            schoolId=request.args.get('schoolId') or None)
