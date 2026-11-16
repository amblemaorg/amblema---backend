# -*- coding: utf-8 -*-
# app/controllers/vademecum/indicator_controller.py
"""Indicadores de uso para el backoffice (API-17)."""

from flask import request
from flask_restful import Resource

from app.helpers.vademecum_auth import vademecum_admin_required
from app.services.vademecum.indicator_service import IndicatorService


class AdminIndicatorsController(Resource):
    @vademecum_admin_required
    def get(self):
        return IndicatorService().summary(request.args)


class AdminIndicatorTeachersController(Resource):
    @vademecum_admin_required
    def get(self):
        return IndicatorService().teachers(request.args)


class AdminIndicatorTeachersExportController(Resource):
    @vademecum_admin_required
    def get(self):
        return IndicatorService().export_teachers(request.args)


class AdminIndicatorTeacherDownloadsController(Resource):
    @vademecum_admin_required
    def get(self, accountId):
        return IndicatorService().teacher_downloads(accountId, request.args)
