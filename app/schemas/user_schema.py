# app/schemas/user_schema.py

from marshmallow import (
    validate, EXCLUDE, pre_load, validates_schema, Schema)

from app.helpers.ma_schema_validators import (
    not_blank, only_letters, only_numbers, validate_email, OneOf, Length)
from app.helpers.ma_schema_validators import ValidationError
from app.helpers.ma_schema_fields import MAReferenceField
from app.models.role_model import Role
from app.models.state_model import State, Municipality
from app.schemas import fields


class UserSchema(Schema):
    id = fields.Str(dump_only=True)
    email = fields.Str(required=True, validate=(validate_email))
    name = fields.Str(dump_only=True)
    password = fields.Str(
        required=True,
        load_only=True,
        validate=(
            not_blank,
            Length(min=8)))
    userType = fields.Str(
        required=True,
        validate=(
            not_blank,
            only_numbers,
            OneOf(
                ["1", "2", "3", "4"],
                ["admin", "coordinator", "sponsor", "school"]

            )))
    phone = fields.Str(validate=only_numbers)
    role = MAReferenceField(required=True, document=Role)
    addressState = MAReferenceField(required=True, document=State)
    addressMunicipality = MAReferenceField(
        required=True, document=Municipality)
    address = fields.Str()
    addressCity = fields.Str()
    status = fields.Str(validate=OneOf(["1", "2"]))
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if 'email' in data and isinstance(data["email"], str):
            data["email"] = str(data["email"]).lower()
        if 'firstName' in data and isinstance(data["firstName"], str):
            data["firstName"] = str(data["firstName"]).title()
        if 'lastName' in data and isinstance(data["lastName"], str):
            data["lastName"] = str(data["lastName"]).title()
        if 'address' in data and isinstance(data["address"], str):
            data["address"] = str(data["address"]).title()
        return data

    @validates_schema
    def validate_cardId_length(self, data, **kwargs):
        errors = {}
        if (
            "cardType" in data
            and str(data["cardType"]) == "1"
            and (len(data["cardId"]) < 7 or len(data["cardId"]) > 8)
        ):
            errors["cardId"] = [{"status": "13", "msg": "Invalid length"}]
        if (
            "cardType" in data
            and str(data["cardType"]) == "2"
            and (len(data["cardId"]) < 8 or len(data["cardId"]) > 9)
        ):
            errors["cardId"] = [{"status": "13", "msg": "Invalid length"}]
        if (
            "cardType" in data
            and str(data["cardType"]) == "3"
            and (len(data["cardId"]) != 10)
        ):
            errors["cardId"] = [{"status": "13", "msg": "Invalid length"}]
        if errors:
            raise ValidationError(errors)

    class Meta:
        unknown = EXCLUDE
        ordered = True
