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
    not_blank, only_letters, only_numbers, OneOf, Range)
from app.helpers.ma_schema_fields import MAReferenceField
from app.models.state_model import State, Municipality


class SchoolContactSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=not_blank)
    code = fields.Str(required=True, validate=not_blank)
    email = fields.Email(required=True)
    address = fields.Str(required=True, validate=not_blank)
    addressState = MAReferenceField(document=State, required=True)
    addressMunicipality = MAReferenceField(
        document=Municipality, required=True)
    addressCity = fields.Str(required=True)
    addressStreet = fields.Str()
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
    subPrincipalFirstName = fields.Str()
    subPrincipalLastName = fields.Str()
    subPrincipalEmail = fields.Email()
    subPrincipalPhone = fields.Str(validate=only_numbers)
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
    sponsorEmail = fields.Email()
    sponsorRIF = fields.Str()
    sponsorAddress = fields.Str()
    sponsorAddressState = MAReferenceField(document=State)
    sponsorAddressMunicipality = MAReferenceField(document=Municipality)
    sponsorAddressCity = fields.Str()
    sponsorAddressStreet = fields.Str()
    sponsorPhone = fields.Str(validate=only_numbers)
    sponsorCompanyType = fields.Str(
        required=True,
        validate=OneOf(
            ('1', '2', '3', '4'),
            ('factory', 'grocery', 'personal business', 'other')
        ))
    sponsorCompanyOtherType = fields.Str()
    sponsorContactFirstName = fields.Str(validate=only_letters)
    sponsorContactLastName = fields.Str(validate=only_letters)
    sponsorContactPhone = fields.Str(validate=only_numbers)
    state = fields.Str(
        default="1",
        validate=OneOf(
            ('1', '2', '3'),
            ('pending', 'acepted', 'rejected')
        ))
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if "email" in data and isinstance(data["email"], str):
            data["email"] = data["email"].lower()
        if "sponsorEmail" in data and isinstance(data["sponsorEmail"], str):
            data["sponsorEmail"] = data["sponsorEmail"].lower()
        toTitle = (
            'name'
            'sponsorName',
            'sponsorAddress',
            'sponsorAddressCity',
            'sponsorAddressStreet',
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
                'sponsorRIF',
                'sponsorAddress',
                'sponsorAddressState',
                'sponsorAddressMunicipality',
                'sponsorAddressCity',
                'sponsorAddressStreet',
                'sponsorPhone',
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
