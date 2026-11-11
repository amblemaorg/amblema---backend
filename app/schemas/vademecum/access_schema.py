# -*- coding: utf-8 -*-
# app/schemas/vademecum/access_schema.py
"""Validación de solicitudes de acceso y su revisión (API-05, GES-03 5.2)."""

from marshmallow import fields

from app.helpers.ma_schema_validators import Length, not_blank, validate_email
from app.schemas.vademecum.auth_schema import _Strict as StrictSchema

NAME_LENGTH = Length(max=60)


class AccessRequestSchema(StrictSchema):
    firstName = fields.Str(required=True, validate=(not_blank, NAME_LENGTH))
    lastName = fields.Str(required=True, validate=(not_blank, NAME_LENGTH))
    email = fields.Str(required=True, validate=(not_blank, validate_email))
    cardId = fields.Str(load_default=None, allow_none=True, validate=Length(max=20))
    phone = fields.Str(load_default=None, allow_none=True, validate=Length(max=20))
    # Texto libre de referencia: no se asocia a ninguna escuela de AmbLeMa
    institution = fields.Str(required=True, validate=(not_blank, Length(max=150)))
    recaptchaToken = fields.Str(load_default=None, allow_none=True)


class RejectSchema(StrictSchema):
    reason = fields.Str(required=True, validate=(not_blank, Length(max=500)))
