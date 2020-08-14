# app/school_contact_schema.py


from marshmallow import (
    Schema,
    fields,
    pre_load,
    EXCLUDE,
    validate,
    validates_schema,
    ValidationError)

from app.helpers.ma_schema_validators import (
    not_blank, only_letters, only_numbers, OneOf, Range, validate_email)
from app.helpers.ma_schema_fields import MAReferenceField, MAPointField
from app.models.state_model import State, Municipality


class SchoolContactSchema(Schema):
    id = fields.Str(dump_only=True)
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
    hasSponsor = fields.Bool(required=True)
    sponsorName = fields.Str()
    sponsorEmail = fields.Str(validate=validate_email)
    sponsorRif = fields.Str()
    sponsorAddress = fields.Str()
    sponsorAddressState = MAReferenceField(document=State)
    sponsorAddressMunicipality = MAReferenceField(document=Municipality)
    sponsorAddressCity = fields.Str()
    sponsorCompanyType = fields.Str(
        validate=OneOf(
            ('0', '1', '2', '3', '4'),
            ('other', 'factory', 'grocery', 'personal business', 'estate')
        ))
    sponsorCompanyOtherType = fields.Str()
    sponsorCompanyPhone = fields.Str(validate=(not_blank, only_numbers))
    sponsorContactFirstName = fields.Str(validate=only_letters)
    sponsorContactLastName = fields.Str(validate=only_letters)
    sponsorContactEmail = fields.Str(validate=validate_email)
    sponsorContactPhone = fields.Str(validate=only_numbers)
    status = fields.Str(
        default="1",
        validate=OneOf(
            ('1', '2', '3'),
            ('pending', 'accepted', 'rejected')
        ))
    createdAt = fields.Function(lambda obj: obj.createdAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z')
    updatedAt = fields.Function(lambda obj: obj.updatedAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z')

    @pre_load
    def process_input(self, data, **kwargs):
        if "email" in data and isinstance(data["email"], str):
            data["email"] = data["email"].lower()
        if "code" in data and isinstance(data['code'], str):
            data["code"] = data["code"].strip().upper()
        if "sponsorEmail" in data and isinstance(data["sponsorEmail"], str):
            data["sponsorEmail"] = data["sponsorEmail"].lower()
        toTitle = (
            'name'
            'sponsorName',
            'sponsorAddressCity',
            'sponsorContactFirstName',
            'sponsorContactLastName')
        for field in toTitle:
            if field in data and isinstance(data[field], str):
                data[field] = data[field].title()
        return data

    @validates_schema
    def validate_schema(self, data, **kwargs):
        errors = {}
        if 'hasSponsor' in data and data['hasSponsor']:
            requiredSponsor = (
                'sponsorName',
                'sponsorEmail',
                'sponsorRif',
                'sponsorAddressState',
                'sponsorAddressMunicipality',
                'sponsorAddressCity',
                'sponsorCompanyPhone',
                'sponsorCompanyType',
                'sponsorContactFirstName',
                'sponsorContactLastName',
                'sponsorContactPhone')
            for required in requiredSponsor:
                if required not in data:
                    errors[required] = ['Field is required']
        if errors:
            raise ValidationError(errors)

    class Meta:
        unknown = EXCLUDE
        ordered = True
