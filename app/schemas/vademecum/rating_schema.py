# -*- coding: utf-8 -*-
# app/schemas/vademecum/rating_schema.py
"""Validación de valoraciones y su moderación (API-16, GES-03 5.4)."""

from marshmallow import fields, validate

from app.helpers.ma_schema_validators import Length
from app.schemas.vademecum.auth_schema import _Strict as StrictSchema


class RatingSchema(StrictSchema):
    stars = fields.Int(required=True, strict=True, validate=validate.Range(min=1, max=5))
    # Vacío o null quita el comentario; las estrellas se guardan igual
    comment = fields.Str(load_default=None, allow_none=True, validate=Length(max=1000))


class ModerationSchema(StrictSchema):
    # Opcional: fecha de la versión que vio el moderador. Si el docente editó después, 409 (120)
    updatedAt = fields.DateTime(load_default=None, allow_none=True)
