# app/schemas/school_user_schema.py


from marshmallow import validate, EXCLUDE

from app.schemas.user_schema import UserSchema
from app.schemas.shared_schemas import ProjectReferenceSchema
from app.schemas import fields
from app.helpers.ma_schema_fields import MAImageField
from app.helpers.ma_schema_validators import (
    not_blank, only_letters, only_numbers, OneOf, Range, validate_image)


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
    image = MAImageField(validate=validate_image,
                         folder='schools')
    schoolType = fields.Str(
        validate=OneOf(
            ('1', '2', '3'),
            ('national', 'statal', 'municipal')
        ))
    principalFirstName = fields.Str()
    principalLastName = fields.Str()
    principalEmail = fields.Email()
    principalPhone = fields.Str(validate=only_numbers)
    subPrincipalFirstName = fields.Str()
    subPrincipalLastName = fields.Str()
    subPrincipalEmail = fields.Email()
    subPrincipalPhone = fields.Str(validate=only_numbers)
    nTeachers = fields.Int(validate=Range(min=0))
    nAdministrativeStaff = fields.Int(
        validate=Range(min=0))
    nLaborStaff = fields.Int(validate=Range(min=0))
    nStudents = fields.Int(validate=Range(min=0))
    nGrades = fields.Int(validate=Range(min=0))
    nSections = fields.Int(validate=Range(min=0))
    schoolShift = fields.Str(
        validate=OneOf(
            ('1', '2', '3'),
            ('morning', 'afternoon', 'both')
        ))
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
