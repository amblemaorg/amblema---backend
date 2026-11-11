# -*- coding: utf-8 -*-
# app/controllers/vademecum/__init__.py
"""Recursos REST del módulo Vademécum. Se registran todos desde register_vademecum_resources."""


def _routes(path):
    """Cada ruta con y sin barra final, como el resto de la API."""
    return (path, path + "/")


def register_vademecum_resources(api):
    from app.controllers.vademecum.auth_controller import (
        RegisterController, VerifyEmailController, ResendVerificationController)

    api.add_resource(RegisterController, *_routes("/vademecum/auth/register"))
    api.add_resource(VerifyEmailController, *_routes("/vademecum/auth/verify-email"))
    api.add_resource(ResendVerificationController,
                     *_routes("/vademecum/auth/resend-verification"))

    from app.controllers.vademecum.session_controller import (
        LoginController, RefreshController, ForgotPasswordController, ResetPasswordController,
        MeController, MePasswordController)

    api.add_resource(LoginController, *_routes("/vademecum/auth/login"))
    api.add_resource(RefreshController, *_routes("/vademecum/auth/refresh"))
    api.add_resource(ForgotPasswordController, *_routes("/vademecum/auth/forgot-password"))
    api.add_resource(ResetPasswordController, *_routes("/vademecum/auth/reset-password"))
    api.add_resource(MeController, *_routes("/vademecum/me"))
    api.add_resource(MePasswordController, *_routes("/vademecum/me/password"))
