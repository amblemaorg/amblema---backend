# -*- coding: utf-8 -*-
# app/services/vademecum/session_service.py
"""Login, renovación, recuperación de contraseña y perfil del docente (API-04)."""

from datetime import datetime

from marshmallow import ValidationError

from app.models.vademecum import VademecumAuthorization, VademecumTeacherAccount
from app.models.vademecum.teacher_account_model import hash_token
from app.schemas.vademecum.auth_schema import (
    ChangePasswordSchema, EmailSchema, LoginSchema, ProfileSchema, TokenPasswordSchema)
from app.services.vademecum import token_service
from app.services.vademecum.account_service import (
    RESET_PASSWORD_PATH, account_dict, error, recently_sent, send_account_email,
    send_verification, session_payload, web_link)
from app.services.vademecum.enrollment_service import EnrollmentService, normalize_email
from app.services.vademecum.recaptcha_service import recaptcha_is_valid

INVALID_CREDENTIALS = ("general", "103", "Invalid email or password")


class SessionService(object):

    def __init__(self, enrollmentService=None):
        self.enrollment = enrollmentService or EnrollmentService()

    def login(self, jsonData):
        try:
            data = LoginSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        if not recaptcha_is_valid(data.get("recaptchaToken")):
            return error("general", "105", "Invalid reCAPTCHA")
        account = VademecumTeacherAccount.objects(
            email=normalize_email(data["email"]), isDeleted=False).first()
        if not account:
            return error(*INVALID_CREDENTIALS)
        if account.status == "pending":
            return error("general", "102", "Email not verified", 403)
        if not account.password_is_valid(data["password"]):
            return error(*INVALID_CREDENTIALS)
        if account.status != "1":
            return error("general", "101", "Account blocked", 403)
        account.lastLoginAt = datetime.utcnow()
        account.save()
        return session_payload(account), 200

    def refresh(self, account):
        """`account` ya validado con el token de renovación."""
        return {"accessToken": token_service.issue_access_token(account)}, 200

    def forgot_password(self, jsonData):
        """Siempre 200 (no revela si el email tiene cuenta)."""
        try:
            data = EmailSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        if not recaptcha_is_valid(data.get("recaptchaToken")):
            return error("general", "105", "Invalid reCAPTCHA")
        account = VademecumTeacherAccount.objects(
            email=normalize_email(data["email"]), isDeleted=False).first()
        if not account:
            return {"msg": "ok"}, 200
        if account.status == "pending":
            # Aún no tiene contraseña: lo que necesita es el enlace de activación
            if not recently_sent(account.emailVerification, token_service.VERIFICATION_LIFETIME):
                send_verification(account)
        elif account.status == "1" and not recently_sent(
                account.passwordReset, token_service.PASSWORD_RESET_LIFETIME):
            raw, accountToken = token_service.new_email_token(
                token_service.PASSWORD_RESET_LIFETIME)
            account.passwordReset = accountToken
            account.save()
            send_account_email(
                account, u"Cambia tu contraseña del Vademécum AmbLeMa",
                u"Recibimos una solicitud para cambiar tu contraseña. Abre este enlace:",
                u"Cambiar mi contraseña", web_link(RESET_PASSWORD_PATH, raw),
                int(token_service.PASSWORD_RESET_LIFETIME.total_seconds() // 3600))
        return {"msg": "ok"}, 200

    def reset_password(self, jsonData):
        try:
            data = TokenPasswordSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        account = VademecumTeacherAccount.objects(
            passwordReset__tokenHash=hash_token(data["token"]), isDeleted=False).first()
        if (not account or account.status != "1"
                or not token_service.email_token_is_valid(account.passwordReset)):
            return error("token", "104", "Invalid or expired link")
        now = datetime.utcnow()
        account.set_password(data["password"])  # invalida los tokens emitidos antes
        account.passwordReset.usedAt = now
        account.lastLoginAt = now
        account.save()
        return session_payload(account), 200

    def change_password(self, account, jsonData):
        try:
            data = ChangePasswordSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        if not account.password_is_valid(data["currentPassword"]):
            return error("currentPassword", "103", "Invalid password")
        account.set_password(data["newPassword"])
        account.save()
        return session_payload(account), 200

    def update_profile(self, account, jsonData):
        try:
            data = ProfileSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        for field in ("firstName", "lastName"):
            if field in data:
                setattr(account, field, data[field])
        account.save()
        return account_dict(account), 200

    def access(self, account):
        """Acceso vigente: matrícula > autorización del año > ninguno (GES-02 4.3).

        La escuela no se guarda en la cuenta: se calcula en cada consulta.
        """
        schoolYear = self.enrollment.current_school_year()
        enrollment = self.enrollment.resolve(account.email, schoolYear)
        access = enrollment.to_dict()
        if enrollment.is_enrolled:
            access["origin"] = "enrollment"
        elif schoolYear and VademecumAuthorization.objects(
                account=account.id, schoolYear=schoolYear.id, revokedAt=None).first():
            access["origin"] = "external"
        else:
            access["origin"] = "none"
        return access

    def me(self, account):
        return {"account": account_dict(account), "access": self.access(account)}, 200
