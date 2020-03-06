# app/schemas/user_schema.py

from marshmallow import (
    validate, EXCLUDE, pre_load, validates_schema, Schema)

from app.helpers.ma_schema_validators import (
    not_blank, validate_email, Length)
from app.helpers.ma_schema_fields import MAReferenceField
from app.schemas import fields
from app.models.user_model import User


class LoginSchema(Schema):
    email = fields.Str(required=True, validate=(validate_email))
    password = fields.Str(
        required=True,
        load_only=True,
        validate=(
            not_blank,
            Length(min=8)))

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @pre_load
    def process_input(self, data, **kwargs):
        if 'email' in data and isinstance(data["email"], str):
            data["email"] = str(data["email"]).lower()
        return data


class RecoverySchema(Schema):
    email = fields.Str(required=True, validate=(validate_email))

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @pre_load
    def process_input(self, data, **kwargs):
        if 'email' in data and isinstance(data["email"], str):
            data["email"] = str(data["email"]).lower()
        return data


class ChangePasswordSchema(Schema):
    user = MAReferenceField(required=True, document=User)
    password = fields.Str(
        required=True,
        load_only=True,
        validate=(
            not_blank,
            Length(min=8)))
    confirmPassword = fields.Str(
        required=True,
        load_only=True,
        validate=(
            not_blank,
            Length(min=8)))

    class Meta:
        unknown = EXCLUDE
        ordered = True
