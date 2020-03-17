# app/schemas/admin_user_schema.py


from marshmallow import fields, validate, EXCLUDE

from app.schemas.user_schema import UserSchema
from app.helpers.ma_schema_validators import (
    not_blank, only_letters, only_numbers, OneOf)


class AdminUserSchema(UserSchema):
    firstName = fields.Str(
        required=True,
        validate=(not_blank, only_letters))
    lastName = fields.Str(
        required=True,
        validate=(not_blank, only_letters))
    cardType = fields.Str(
        required=True,
        validate=(
            not_blank,
            OneOf(
                ["1", "2", "3"],
                ["v", "j", "e"]
            )))
    cardId = fields.Str(
        required=True,
        validate=(not_blank, only_numbers))
    phone = fields.Str(validate=only_numbers)
    function = fields.Str(
        required=True,
        validate=(not_blank, only_letters))

    class Meta:
        unknown = EXCLUDE
        ordered = True
