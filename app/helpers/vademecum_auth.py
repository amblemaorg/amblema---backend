# -*- coding: utf-8 -*-
# app/helpers/vademecum_auth.py
"""Decoradores del docente de Vademécum (GES-03 4.1).

A diferencia de jwt_required, no se saltan en TESTING: las pruebas generan tokens reales.
"""

from functools import wraps

from bson import ObjectId
from bson.errors import InvalidId
from flask import g, request

from app.models.vademecum import VademecumTeacherAccount
from app.services.vademecum import token_service

UNAUTHORIZED = ({"general": [{"status": "100", "msg": "Invalid or expired token"}]}, 401)
BLOCKED = ({"general": [{"status": "101", "msg": "Account blocked"}]}, 403)


def bearer_token():
    header = request.headers.get("Authorization", "")
    parts = header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def account_from_token(kind):
    """(cuenta, None) o (None, respuesta de error) para el token del encabezado."""
    token = bearer_token()
    if not token:
        return None, UNAUTHORIZED
    try:
        payload = token_service.decode_token(token, kind)
        accountId = ObjectId(payload["sub"])
    except (token_service.InvalidTeacherToken, InvalidId, TypeError):
        return None, UNAUTHORIZED
    account = VademecumTeacherAccount.objects(id=accountId, isDeleted=False).first()
    if not account or account.status == "pending":
        return None, UNAUTHORIZED
    if token_service.issued_before_password_change(payload, account):
        return None, UNAUTHORIZED
    if account.status != "1":
        return None, BLOCKED
    return account, None


def vademecum_teacher_required(fn):
    """Exige un token de acceso de docente válido; deja la cuenta en g.vademecum_account."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        account, failure = account_from_token("access")
        if failure:
            return failure
        g.vademecum_account = account
        return fn(*args, **kwargs)
    return wrapper


def vademecum_teacher_optional(fn):
    """Como el anterior, pero sin token o con uno inválido sigue como visitante (None)."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        account = None
        if bearer_token():
            account, _ = account_from_token("access")
        g.vademecum_account = account
        return fn(*args, **kwargs)
    return wrapper


def vademecum_admin_required(fn):
    """Token del backoffice con el permiso `vademecum_admin` (BO-01) en su rol activo.

    Deja el usuario en g.vademecum_admin. No se salta en TESTING (el módulo guarda quién hizo
    cada acción) y nunca acepta un token de docente (otro secreto). El permiso se lee del rol
    en la BD, no del token: quitarlo en "Roles" corta el acceso sin esperar a que el token
    venza.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from flask_jwt_extended.view_decorators import verify_jwt_in_request
        from app.helpers.handler_authorization import get_current_user
        from app.helpers.vademecum_seeds import PERMISSION_ACTION
        verify_jwt_in_request()
        try:
            user = get_current_user()
        except AttributeError:  # identidad que no es la de un usuario del backoffice
            user = None
        if not user or not user.role or PERMISSION_ACTION not in user.get_permissions():
            return {"msg": "No authorized"}, 403
        g.vademecum_admin = user
        return fn(*args, **kwargs)
    return wrapper
