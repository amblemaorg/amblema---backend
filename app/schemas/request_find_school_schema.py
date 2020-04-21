# app/request_find_school_schema.py


from marshmallow import Schema, fields

from app.models.user_model import User
from app.models.project_model import Project
from app.models.state_model import State, Municipality
from app.helpers.ma_schema_fields import MAReferenceField
from app.helpers.ma_schema_validators import not_blank, only_numbers, OneOf, Range


class ReqFindSchoolSchema(Schema):
    id = fields.Str(dump_only=True)
    project = MAReferenceField(required=True, document=Project, field="code")
    user = MAReferenceField(required=True, document=User, field="name")
    requestCode = fields.Function(lambda obj: obj.requestCode.zfill(7))
    name = fields.Str(required=True, validate=not_blank)
    code = fields.Str(required=True, validate=not_blank)
    email = fields.Email(required=True)
    address = fields.Str()
    addressState = MAReferenceField(document=State, required=True)
    addressMunicipality = MAReferenceField(
        document=Municipality, required=True)
    addressCity = fields.Str()
    addressZoneType = fields.Str(
        allow_none=True,
        validate=OneOf(
            ('1', '2', '3'),
            ('sector', 'neighborhood', 'hamlet')
        ))
    addressZone = fields.Str(allow_none=True)
    phone = fields.Str(required=True, validate=(not_blank, only_numbers))
    schoolType = fields.Str(
        required=True,
        validate=OneOf(
            ('1', '2', '3'),
            ('national', 'statal', 'municipal')
        ))
    principalFirstName = fields.Str(required=True)
    principalLastName = fields.Str(required=True)
    principalEmail = fields.Email(required=True)
    principalPhone = fields.Str(required=True, validate=only_numbers)
    subPrincipalFirstName = fields.Str(allow_none=True)
    subPrincipalLastName = fields.Str(allow_none=True)
    subPrincipalEmail = fields.Email(allow_none=True)
    subPrincipalPhone = fields.Str(validate=only_numbers, allow_none=True)
    nTeachers = fields.Int(required=True, validate=Range(min=0))
    nAdministrativeStaff = fields.Int(
        required=True, validate=Range(min=0))
    nLaborStaff = fields.Int(required=True, validate=Range(min=0))
    nStudents = fields.Int(required=True, validate=Range(min=0))
    nGrades = fields.Int(required=True, validate=Range(min=0))
    nSections = fields.Int(required=True, validate=Range(min=0))
    schoolShift = fields.Str(
        required=True,
        validate=OneOf(
            ('1', '2', '3'),
            ('morning', 'afternoon', 'both')
        ))
