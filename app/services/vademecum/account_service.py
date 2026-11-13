# -*- coding: utf-8 -*-
# app/services/vademecum/account_service.py
"""Registro y verificación de email del docente (API-03, GES-03 5.1).

La cuenta nace "pending" y sin contraseña; solo el enlace del correo la activa (status "1").
Login, descargas y todo /me exigen status "1", así que la primera descarga exige email
verificado.
"""

from datetime import datetime, timedelta

from flask import current_app
from marshmallow import ValidationError
from mongoengine import NotUniqueError

from app.helpers.handler_emails import send_email
from app.models.vademecum import VademecumTeacherAccount
from app.models.vademecum.teacher_account_model import hash_token
from app.schemas.vademecum.auth_schema import RegisterSchema, EmailSchema, TokenPasswordSchema
from app.services.vademecum import token_service
from app.services.vademecum.enrollment_service import EnrollmentService, normalize_email
from app.services.vademecum.recaptcha_service import recaptcha_is_valid

# Rutas de la web docente que reciben el token del correo (las implementa WEB-06/WEB-07)
VERIFY_EMAIL_PATH = "/verificar-email"
RESET_PASSWORD_PATH = "/restablecer-contrasena"
# No se reenvía un enlace si el anterior se emitió hace menos de esto
RESEND_THROTTLE = timedelta(minutes=1)


def error(field, code, msg, httpStatus=400):
    return {field: [{"status": code, "msg": msg}]}, httpStatus


def isoformat(value):
    return value.replace(microsecond=0).isoformat() + "Z" if value else None


def account_dict(account):
    return {"id": str(account.id), "email": account.email, "firstName": account.firstName,
            "lastName": account.lastName, "emailVerifiedAt": isoformat(account.emailVerifiedAt)}


def session_payload(account):
    return {"accessToken": token_service.issue_access_token(account),
            "refreshToken": token_service.issue_refresh_token(account),
            "account": account_dict(account)}


def web_link(path, token):
    base = (current_app.config.get("VADEMECUM_WEB_URL") or "").rstrip("/")
    return "{}{}?token={}".format(base, path, token)


def send_account_email(account, subject, intro, buttonText, link, hours):
    """Envía el correo; un fallo se registra y no rompe el flujo (se puede reenviar)."""
    name = account.firstName or ""
    html = (u"<p>Hola {name},</p><p>{intro}</p>"
            u"<p><a href=\"{link}\">{button}</a></p>"
            u"<p>El enlace vence en {hours} horas. Si no fuiste tú, ignora este correo.</p>"
            u"<p>Vademécum AmbLeMa</p>").format(name=name, intro=intro, link=link,
                                               button=buttonText, hours=hours)
    text = (u"Hola {name},\n\n{intro}\n\n{link}\n\nEl enlace vence en {hours} horas. "
            u"Si no fuiste tú, ignora este correo.\n\nVademécum AmbLeMa").format(
                name=name, intro=intro, link=link, hours=hours)
    try:
        result = send_email(html, text, subject, account.email)
    except Exception:
        current_app.logger.exception("Vademecum: email to account %s failed", account.id)
        return False
    if result is not True:
        current_app.logger.error("Vademecum: email to account %s failed: %s", account.id, result)
        return False
    return True


def send_verification(account):
    raw, accountToken = token_service.new_email_token(token_service.VERIFICATION_LIFETIME)
    account.emailVerification = accountToken
    account.save()
    hours = int(token_service.VERIFICATION_LIFETIME.total_seconds() // 3600)
    return send_account_email(
        account, u"Activa tu cuenta del Vademécum AmbLeMa",
        u"Para activar tu cuenta y crear tu contraseña, abre este enlace:",
        u"Crear mi contraseña", web_link(VERIFY_EMAIL_PATH, raw), hours)


def recently_sent(accountToken, lifetime):
    if not accountToken or accountToken.usedAt:
        return False
    issuedAt = accountToken.expiresAt - lifetime
    return datetime.utcnow() - issuedAt < RESEND_THROTTLE


class AccountService(object):

    def __init__(self, enrollmentService=None):
        self.enrollment = enrollmentService or EnrollmentService()

    def register(self, jsonData):
        try:
            data = RegisterSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        if not recaptcha_is_valid(data.get("recaptchaToken")):
            return error("general", "105", "Invalid reCAPTCHA")
        schoolYear = self.enrollment.current_school_year()
        if not schoolYear:
            return error("general", "117", "No current school year", 409)

        email = normalize_email(data["email"])
        account = VademecumTeacherAccount.objects(email=email).first()
        if account:
            if account.isDeleted or account.status != "pending":
                return {"result": "account_exists"}, 200
            # Cuenta pendiente (registro previo o solicitud aprobada): se reenvía el enlace
            if not recently_sent(account.emailVerification, token_service.VERIFICATION_LIFETIME):
                send_verification(account)
            return {"result": "verification_sent"}, 200

        if not self.enrollment.resolve(email, schoolYear).is_enrolled:
            return {"result": "not_enrolled"}, 200

        account = VademecumTeacherAccount(
            email=email, firstName=data["firstName"], lastName=data["lastName"],
            status="pending")
        try:
            account.save()
        except NotUniqueError:  # dos registros simultáneos del mismo email
            return {"result": "verification_sent"}, 200
        send_verification(account)
        return {"result": "verification_sent"}, 200

    def resend_verification(self, jsonData):
        """Siempre 200 (no revela si el email tiene cuenta)."""
        try:
            data = EmailSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        account = VademecumTeacherAccount.objects(
            email=normalize_email(data["email"]), status="pending", isDeleted=False).first()
        if account and not recently_sent(account.emailVerification,
                                         token_service.VERIFICATION_LIFETIME):
            send_verification(account)
        return {"msg": "ok"}, 200

    def verify_email(self, jsonData):
        try:
            data = TokenPasswordSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        account = VademecumTeacherAccount.objects(
            emailVerification__tokenHash=hash_token(data["token"]), isDeleted=False).first()
        if (not account or account.status != "pending"
                or not token_service.email_token_is_valid(account.emailVerification)):
            return error("token", "104", "Invalid or expired link")
        now = datetime.utcnow()
        account.set_password(data["password"])
        account.status = "1"
        account.emailVerifiedAt = now
        account.emailVerification.usedAt = now
        account.lastLoginAt = now
        account.save()
        return session_payload(account), 200
