# app/schemas/school_user_schema.py


from marshmallow import validate, EXCLUDE

from app.schemas.user_schema import UserSchema
from app.schemas.shared_schemas import ProjectReferenceSchema
from app.schemas import fields
from app.helpers.ma_schema_validators import (
    not_blank, only_letters, only_numbers, OneOf)


class SchoolUserSchema(UserSchema):
    code = fields.Str(
        required=True,
        validate=(not_blank))
    name = fields.Str(
        required=True,
        validate=(not_blank))
    contactFirstName = fields.Str(
        required=True,
        validate=(not_blank, only_letters))
    contactLastName = fields.Str(
        required=True,
        validate=(not_blank, only_letters))
    contactEmail = fields.Email(required=True)
    contactPhone = fields.Str(
        required=True,
        validate=(not_blank, only_numbers))
    contactFunction = fields.Str(required=True)
    status = fields.Str(
        validate=OneOf(
            ("1", "2", "3"),
            ("interested", "active", "inactive")
        )
    )
    project = fields.Nested(ProjectReferenceSchema, dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True
