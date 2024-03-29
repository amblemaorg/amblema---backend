# app/schemas/sponsor_user_schema.py


from marshmallow import fields, validate, EXCLUDE

from app.schemas.user_schema import UserSchema
from app.schemas.shared_schemas import ProjectReferenceSchema
from app.helpers.ma_schema_validators import (
    not_blank, only_letters, only_numbers, OneOf, validate_image, validate_url, validate_email)
from app.helpers.ma_schema_fields import MAImageField


class SponsorUserSchema(UserSchema):
    name = fields.Str(
        required=True,
        validate=(not_blank))
    companyRif = fields.Str(required=True, validate=only_numbers)
    companyType = fields.Str(
        required=True,
        validate=OneOf(
            ('0', '1', '2', '3', '4'),
            ('other', 'factory', 'grocery', 'personal business', 'estate')
        ))
    companyOtherType = fields.Str()
    companyPhone = fields.Str(required=True, validate=only_numbers)
    contactFirstName = fields.Str(validate=only_letters)
    contactLastName = fields.Str(validate=only_letters)
    contactEmail = fields.Str(validate=validate_email)
    contactPhone = fields.Str(required=True, validate=only_numbers)
    image = MAImageField(
        allow_none=True,
        validate=validate_image,
        folder='sponsors')
    webSite = fields.Str(validate=validate_url)
    status = fields.Str(
        validate=OneOf(
            ("1", "2"),
            ("active", "inactive")
        )
    )
    phase = fields.Str(
        validate=OneOf(
            ("1", "2", "3"),
            ("initial", "interested", "peca")
        )
    )
    projects = fields.List(fields.Nested(
        ProjectReferenceSchema), dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True
