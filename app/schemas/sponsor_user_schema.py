# app/schemas/sponsor_user_schema.py


from marshmallow import fields, validate, EXCLUDE

from app.schemas.user_schema import UserSchema
from app.schemas.shared_schemas import ProjectReferenceSchema
from app.helpers.ma_schema_validators import (
    not_blank, only_letters, only_numbers)


class SponsorUserSchema(UserSchema):
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
    companyRIF = fields.Str(required=True, validate=only_numbers)
    companyType = fields.Str(
        required=True,
        validate=validate.OneOf(
            ('1', '2', '3', '4'),
            ('factory', 'grocery', 'personal business', 'other')
        ))
    companyPhone = fields.Str(required=True, validate=only_numbers)
    contactName = fields.Str(required=True, validate=only_letters)
    contactPhone = fields.Str(required=True, validate=only_numbers)
    schools = fields.List(fields.Nested(
        ProjectReferenceSchema), dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True
