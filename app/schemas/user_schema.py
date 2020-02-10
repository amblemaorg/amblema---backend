# app/schemas/user_schema.py

from marshmallow import (
    fields, validate, EXCLUDE, pre_load, validates_schema, Schema)

from app.helpers.ma_schema_validators import (
    not_blank, only_letters, only_numbers)
from app.helpers.ma_schema_validators import ValidationError
from app.helpers.ma_schema_fields import MAReferenceField
from app.models.role_model import Role
from app.models.state_model import State, Municipality


class UserSchema(Schema):
    id = fields.Str(dump_only=True)
    email = fields.Email(required=True, validate=not_blank)
    password = fields.Str(
        required=True,
        load_only=True,
        validate=(
            not_blank,
            validate.Length(equal=8)))
    userType = fields.Str(
        required=True,
        validate=(
            not_blank,
            only_numbers,
            validate.OneOf(
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
    state = fields.Str(validate=validate.OneOf(["1", "2"]))
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if 'email' in data:
            data["email"] = str(data["email"]).lower()
        if 'firstName' in data:
            data["firstName"] = str(data["firstName"]).title()
        if 'lastName' in data:
            data["lastName"] = str(data["lastName"]).title()
        if 'address' in data:
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
            errors["cardId"] = ["Invalid field length"]
        if (
            "cardType" in data
            and str(data["cardType"]) == "2"
            and (len(data["cardId"]) < 8 or len(data["cardId"]) > 9)
        ):
            errors["cardId"] = ["Invalid field length"]
        if (
            "cardType" in data
            and str(data["cardType"]) == "3"
            and (len(data["cardId"]) != 10)
        ):
            errors["cardId"] = ["Invalid field length"]
        if errors:
            raise ValidationError(errors)

    class Meta:
        unknown = EXCLUDE
        ordered = True
