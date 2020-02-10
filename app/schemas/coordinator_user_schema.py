# app/schemas/coordinator_user_schema.py


from marshmallow import fields, validate, EXCLUDE

from app.schemas.user_schema import UserSchema
from app.schemas.shared_schemas import ProjectReferenceSchema
from app.helpers.ma_schema_validators import (
    not_blank, only_letters, only_numbers)


class CoordinatorUserSchema(UserSchema):
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
            validate.OneOf(
                ["1", "2", "3"],
                ["v", "j", "e"]
            )))
    cardId = fields.Str(
        required=True,
        validate=(not_blank, only_numbers))
    birthdate = fields.Date(required=True)
    schools = fields.List(fields.Nested(
        ProjectReferenceSchema), dump_only=True)
    homePhone = fields.Str(required=True, validate=only_numbers)
    addressHouse = fields.Str()

    class Meta:
        unknown = EXCLUDE
        ordered = True
