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
