# -*- coding: utf-8 -*-
# app/services/vademecum/token_service.py
"""Tokens de docente (GES-03 4.1) y enlaces de correo.

Se firman con VADEMECUM_JWT_SECRET_KEY con PyJWT directo, sin JWTManager: un token de docente
nunca valida en jwt_required/admin_required, y uno del backoffice nunca valida aquí.
"""

import base64
import calendar
import os
from datetime import datetime, timedelta

import jwt
from flask import current_app

from app.models.vademecum.teacher_account_model import AccountToken, hash_token

TOKEN_TYPE = "vademecum_teacher"
ALGORITHM = "HS256"
ACCESS_LIFETIME = timedelta(hours=1)
REFRESH_LIFETIME = timedelta(days=30)
VERIFICATION_LIFETIME = timedelta(hours=48)
PASSWORD_RESET_LIFETIME = timedelta(hours=1)


class InvalidTeacherToken(Exception):
    pass


def _secret():
    secret = current_app.config.get("VADEMECUM_JWT_SECRET_KEY")
    # Sin secreto propio, o igual al del backoffice, no se emite ni se acepta ningún token
    if not secret or secret == current_app.config.get("SECRET_KEY"):
        raise RuntimeError("VADEMECUM_JWT_SECRET_KEY missing or equal to JWT_SECRET_KEY")
    return secret


def _timestamp(value):
    return calendar.timegm(value.utctimetuple())


def _issue(account, kind, lifetime):
    now = datetime.utcnow()
    payload = {"sub": str(account.id), "type": TOKEN_TYPE, "kind": kind,
               "iat": _timestamp(now), "exp": _timestamp(now + lifetime)}
    token = jwt.encode(payload, _secret(), algorithm=ALGORITHM)
    return token.decode("utf-8") if isinstance(token, bytes) else token


def issue_access_token(account):
    return _issue(account, "access", ACCESS_LIFETIME)


def issue_refresh_token(account):
    return _issue(account, "refresh", REFRESH_LIFETIME)


def decode_token(token, kind):
    """Payload de un token válido del tipo pedido; si no, InvalidTeacherToken."""
    try:
        payload = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        raise InvalidTeacherToken()
    if payload.get("type") != TOKEN_TYPE or payload.get("kind") != kind or not payload.get("sub"):
        raise InvalidTeacherToken()
    return payload


def issued_before_password_change(payload, account):
    """True si el token es anterior al último cambio de contraseña (queda invalidado)."""
    if not account.passwordChangedAt:
        return False
    return int(payload.get("iat", 0)) < _timestamp(account.passwordChangedAt)


def new_email_token(lifetime):
    """(token en claro para el enlace, AccountToken con solo el hash)."""
    raw = base64.urlsafe_b64encode(os.urandom(32)).decode("ascii").rstrip("=")
    return raw, AccountToken(tokenHash=hash_token(raw), expiresAt=datetime.utcnow() + lifetime)


def email_token_is_valid(accountToken):
    return bool(accountToken and not accountToken.usedAt
                and accountToken.expiresAt > datetime.utcnow())
