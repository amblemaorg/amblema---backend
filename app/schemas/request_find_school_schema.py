# app/request_find_school_schema.py


from marshmallow import Schema, fields, pre_load

from app.models.user_model import User
from app.models.project_model import Project
from app.models.state_model import State, Municipality
from app.helpers.ma_schema_fields import MAReferenceField, MAPointField
from app.helpers.ma_schema_validators import not_blank, only_numbers, OneOf, Range, validate_email


class ReqFindSchoolSchema(Schema):
    id = fields.Str(dump_only=True)
    project = MAReferenceField(required=True, document=Project, field="code")
    user = MAReferenceField(required=True, document=User, field="name")
    requestCode = fields.Function(lambda obj: obj.requestCode.zfill(7))
    name = fields.Str(required=True, validate=not_blank)
    code = fields.Str(required=True, validate=not_blank)
    email = fields.Str(required=True, validate=validate_email)
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
    coordinate = MAPointField()
    phone = fields.Str(required=True, validate=(not_blank, only_numbers))
    schoolType = fields.Str(
        required=True,
        validate=OneOf(
            ('1', '2', '3'),
            ('national', 'statal', 'municipal')
        ))
    principalFirstName = fields.Str(required=True)
    principalLastName = fields.Str(required=True)
    principalEmail = fields.Str(required=True, validate=validate_email)
    principalPhone = fields.Str(required=True, validate=only_numbers)
    subPrincipalFirstName = fields.Str(allow_none=True)
    subPrincipalLastName = fields.Str(allow_none=True)
    subPrincipalEmail = fields.Str(allow_none=True, validate=validate_email)
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
    status = fields.Str(
        default="1",
        validate=OneOf(
            ('1', '2', '3'),
            ('pending', 'accepted', 'rejected')
        ))
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if "code" in data and isinstance(data['code'], str):
            data["code"] = data["code"].strip().upper()
        if "email" in data and isinstance(data['email'], str):
            data["email"] = data["email"].strip().lower()
