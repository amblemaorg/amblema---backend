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
    phone = fields.Str(validate=only_numbers)
    image = MAImageField(allow_none=True, validate=validate_image,
                         folder='schools')
    schoolType = fields.Str(
        allow_none=True,
        validate=OneOf(
            ('1', '2', '3'),
            ('national', 'statal', 'municipal')
        ))
    addressZoneType = fields.Str(
        allow_none=True,
        validate=OneOf(
            ('1', '2', '3'),
            ('sector', 'neighborhood', 'hamlet')
        ))
    addressZone = fields.Str(allow_none=True)
    principalFirstName = fields.Str()
    principalLastName = fields.Str()
    principalEmail = fields.Email()
    principalPhone = fields.Str(validate=only_numbers)
    subPrincipalFirstName = fields.Str(allow_none=True)
    subPrincipalLastName = fields.Str(allow_none=True)
    subPrincipalEmail = fields.Email(allow_none=True)
    subPrincipalPhone = fields.Str(allow_none=True, validate=only_numbers)
    nTeachers = fields.Int(allow_none=True, validate=Range(min=0))
    nAdministrativeStaff = fields.Int(allow_none=True,
                                      validate=Range(min=0))
    nLaborStaff = fields.Int(allow_none=True, validate=Range(min=0))
    nStudents = fields.Int(allow_none=True, validate=Range(min=0))
    nGrades = fields.Int(allow_none=True, validate=Range(min=0))
    nSections = fields.Int(allow_none=True, validate=Range(min=0))
    schoolShift = fields.Str(
        allow_none=True,
        validate=OneOf(
            ('1', '2', '3'),
            ('morning', 'afternoon', 'both')
        ))
    status = fields.Str(
        validate=OneOf(
            ("1", "2"),
            ("active", "inactive")
        )
    )
    phase = fields.Str(
        default="1",
        validate=OneOf(
            ("1", "2", "3"),
            ("initial", "interested", "peca")
        )
    )
    project = fields.Nested(ProjectReferenceSchema, dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True
