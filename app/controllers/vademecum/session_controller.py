# -*- coding: utf-8 -*-
# app/controllers/vademecum/session_controller.py
"""Sesión y perfil del docente: /vademecum/auth/{login,refresh,...} y /vademecum/me."""

from flask import g, request
from flask_restful import Resource

from app.helpers.vademecum_auth import account_from_token, vademecum_teacher_required
from app.services.vademecum.session_service import SessionService


class LoginController(Resource):
    def post(self):
        return SessionService().login(request.get_json(silent=True))


class RefreshController(Resource):
    def post(self):
        account, failure = account_from_token("refresh")
        if failure:
            return failure
        return SessionService().refresh(account)


class ForgotPasswordController(Resource):
    def post(self):
        return SessionService().forgot_password(request.get_json(silent=True))


class ResetPasswordController(Resource):
    def post(self):
        return SessionService().reset_password(request.get_json(silent=True))


class MeController(Resource):
    @vademecum_teacher_required
    def get(self):
        return SessionService().me(g.vademecum_account)

    @vademecum_teacher_required
    def put(self):
        return SessionService().update_profile(g.vademecum_account,
                                               request.get_json(silent=True))


class MePasswordController(Resource):
    @vademecum_teacher_required
    def put(self):
        return SessionService().change_password(g.vademecum_account,
                                                request.get_json(silent=True))
