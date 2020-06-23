# app/sponsor_contact_schema.py


from marshmallow import (
    Schema,
    fields,
    pre_load,
    EXCLUDE,
    validate,
    validates_schema,
    ValidationError)

from app.helpers.ma_schema_validators import not_blank, only_numbers, OneOf, Range, validate_email
from app.helpers.ma_schema_fields import MAReferenceField
from app.models.state_model import State, Municipality
from app.schemas.shared_schemas import CoordinateSchema


class SponsorContactSchema(Schema):
    id = fields.Str(dump_only=True)
    requestCode = fields.Function(lambda obj: obj.requestCode.zfill(7))
    name = fields.Str(required=True, validate=not_blank)
    email = fields.Str(required=True, validate=(not_blank, validate_email))
    rif = fields.Str(required=True, validate=only_numbers)
    companyType = fields.Str(
        required=True,
        validate=OneOf(
            ('0', '1', '2', '3', '4'),
            ('other', 'factory', 'grocery', 'personal business', 'estate')
        ))
    companyOtherType = fields.Str()
    companyPhone = fields.Str(required=True, validate=only_numbers)
    address = fields.Str()
    addressState = MAReferenceField(required=True, document=State)
    addressMunicipality = MAReferenceField(
        required=True, document=Municipality)
    addressCity = fields.Str()
    contactFirstName = fields.Str(validate=not_blank)
    contactLastName = fields.Str(validate=not_blank)
    contactEmail = fields.Str(validate=validate_email)
    contactPhone = fields.Str(required=True, validate=not_blank)
    hasSchool = fields.Bool()
    schoolName = fields.Str(validate=not_blank)
    schoolCode = fields.Str(validate=not_blank)
    schoolEmail = fields.Str(validate=validate_email)
    schoolAddress = fields.Str()
    schoolAddressState = MAReferenceField(document=State)
    schoolAddressMunicipality = MAReferenceField(
        document=Municipality)
    schoolAddressCity = fields.Str()
    schoolAddressZoneType = fields.Str(
        allow_none=True,
        validate=OneOf(
            ('1', '2', '3'),
            ('sector', 'neighborhood', 'hamlet')
        ))
    schoolAddressZone = fields.Str(allow_none=True)
    schoolCoordinate = fields.Nested(CoordinateSchema)
    schoolPhone = fields.Str(validate=(not_blank, only_numbers))
    schoolType = fields.Str(
        validate=OneOf(
            ('1', '2', '3'),
            ('national', 'statal', 'municipal')
        ))
    schoolPrincipalFirstName = fields.Str()
    schoolPrincipalLastName = fields.Str()
    schoolPrincipalEmail = fields.Str(validate=validate_email)
    schoolPrincipalPhone = fields.Str(validate=only_numbers)
    schoolSubPrincipalFirstName = fields.Str(allow_none=True)
    schoolSubPrincipalLastName = fields.Str(allow_none=True)
    schoolSubPrincipalEmail = fields.Str(
        allow_none=True, validate=validate_email)
    schoolSubPrincipalPhone = fields.Str(
        allow_none=True, validate=only_numbers)
    schoolNTeachers = fields.Int(validate=Range(min=0))
    schoolNAdministrativeStaff = fields.Int(
        validate=Range(min=0))
    schoolNLaborStaff = fields.Int(validate=Range(min=0))
    schoolNStudents = fields.Int(validate=Range(min=0))
    schoolNGrades = fields.Int(validate=Range(min=0))
    schoolNSections = fields.Int(validate=Range(min=0))
    schoolShift = fields.Str(
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
        if "email" in data and isinstance(data["email"], str):
            data["email"] = data["email"].lower()
        if "schoolEmail" in data and isinstance(data["schoolEmail"], str):
            data["schoolEmail"] = data["schoolEmail"].lower()

        toTitle = (
            'name'
            'schoolAddressCity',
            'schoolPrincipalFirstName',
            'schoolPrincipalLastName',
            'schoolSubPrincipalFirstName',
            'schoolSubPrincipalFirstName')
        for field in toTitle:
            if field in data and isinstance(data[field], str):
                data[field] = data[field].title()
        return data

    @validates_schema
    def validate_schema(self, data, **kwargs):
        errors = {}
        if 'hasSchool' in data and data['hasSchool']:
            requiredSchool = (
                'schoolName',
                'schoolCode',
                'schoolEmail',
                'schoolAddressState',
                'schoolAddressMunicipality',
                'schoolAddressCity',
                'schoolPhone',
                'schoolType',
                'schoolPrincipalFirstName',
                'schoolPrincipalLastName',
                'schoolPrincipalEmail',
                'schoolPrincipalPhone',
                'schoolSubPrincipalFirstName',
                'schoolSubPrincipalLastName',
                'schoolSubPrincipalEmail',
                'schoolSubPrincipalPhone',
                'schoolNTeachers',
                'schoolNAdministrativeStaff',
                'schoolNLaborStaff',
                'schoolNStudents',
                'schoolNGrades',
                'schoolNSections',
                'schoolShift'
            )
            for required in requiredSchool:
                if required not in data:
                    errors[required] = ['Field is required']
        if errors:
            raise ValidationError(errors)

    class Meta:
        unknown = EXCLUDE
        ordered = True
