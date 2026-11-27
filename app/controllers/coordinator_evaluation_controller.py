# -*- coding: utf-8 -*-
# app/controllers/coordinator_evaluation_controller.py

from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import verify_jwt_in_request_optional, get_jwt_identity

from app.services.coordinator_evaluation_service import CoordinatorEvaluationService
from app.helpers.handler_authorization import jwt_required, get_current_user


def _caller():
    if current_app.config.get("TESTING"):
        verify_jwt_in_request_optional()
        if not get_jwt_identity():
            return None
    return get_current_user()


class CoordinatorEvaluationController(Resource):

    service = CoordinatorEvaluationService()

    @jwt_required
    def get(self, pecaId):
        return self.service.get_evaluation(pecaId, caller=_caller())

    @jwt_required
    def post(self, pecaId):
        return self.service.save_evaluation(
            pecaId, request.get_json(silent=True), caller=_caller())
