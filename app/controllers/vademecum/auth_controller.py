# -*- coding: utf-8 -*-
# app/controllers/vademecum/auth_controller.py
"""Autenticación del docente (rutas públicas /vademecum/auth/...)."""

from flask import request
from flask_restful import Resource

from app.services.vademecum.account_service import AccountService


class RegisterController(Resource):
    def post(self):
        return AccountService().register(request.get_json(silent=True))


class VerifyEmailController(Resource):
    def post(self):
        return AccountService().verify_email(request.get_json(silent=True))


class ResendVerificationController(Resource):
    def post(self):
        return AccountService().resend_verification(request.get_json(silent=True))
