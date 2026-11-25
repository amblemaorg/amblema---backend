# -*- coding: utf-8 -*-
# app/schemas/vademecum/auth_schema.py
"""Validación de los payloads de autenticación del docente (GES-03)."""

from marshmallow import EXCLUDE, Schema, ValidationError, fields, pre_load, validates_schema

from app.helpers.ma_schema_validators import Length, not_blank, validate_email

NAME_LENGTH = Length(max=60)
PASSWORD_LENGTH = Length(min=8, max=64)


class _Strict(Schema):
    class Meta:
        unknown = EXCLUDE

    @pre_load
    def strip_strings(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        return {k: (v.strip() if isinstance(v, str) and k != "password" else v)
                for k, v in data.items()}


class RegisterSchema(_Strict):
    firstName = fields.Str(load_default=None, allow_none=True, validate=(not_blank, NAME_LENGTH))
    lastName = fields.Str(load_default=None, allow_none=True, validate=(not_blank, NAME_LENGTH))
    schoolId = fields.Str(load_default=None, allow_none=True, validate=not_blank)
    email = fields.Str(required=True, validate=(not_blank, validate_email))
    recaptchaToken = fields.Str(load_default=None, allow_none=True)

    @validates_schema(skip_on_field_errors=False)
    def require_names_without_school(self, data, **kwargs):
        if data.get("schoolId"):
            return
        errors = {}
        if not data.get("firstName"):
            errors["firstName"] = [{"status": "2", "msg": "Missing data for required field."}]
        if not data.get("lastName"):
            errors["lastName"] = [{"status": "2", "msg": "Missing data for required field."}]
        if errors:
            raise ValidationError(errors)


class EmailSchema(_Strict):
    email = fields.Str(required=True, validate=(not_blank, validate_email))
    recaptchaToken = fields.Str(load_default=None, allow_none=True)


class TokenPasswordSchema(_Strict):
    token = fields.Str(required=True, validate=not_blank)
    password = fields.Str(required=True, validate=(not_blank, PASSWORD_LENGTH))


class LoginSchema(_Strict):
    email = fields.Str(required=True, validate=(not_blank, validate_email))
    password = fields.Str(required=True, validate=not_blank)
    recaptchaToken = fields.Str(load_default=None, allow_none=True)


class ProfileSchema(_Strict):
    firstName = fields.Str(validate=(not_blank, NAME_LENGTH))
    lastName = fields.Str(validate=(not_blank, NAME_LENGTH))


class ChangePasswordSchema(_Strict):
    currentPassword = fields.Str(required=True, validate=not_blank)
    newPassword = fields.Str(required=True, validate=(not_blank, PASSWORD_LENGTH))
