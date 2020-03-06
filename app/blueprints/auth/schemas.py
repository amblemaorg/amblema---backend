# app/schemas/user_schema.py

from marshmallow import (
    validate, EXCLUDE, pre_load, validates_schema, Schema)

from app.helpers.ma_schema_validators import (
    not_blank, validate_email, Length)

from app.schemas import fields


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
