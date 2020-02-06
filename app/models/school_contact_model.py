# /app/models/school_contact_model.py


from datetime import datetime
import json

from mongoengine import (
    Document,
    StringField,
    EmailField,
    URLField,
    BooleanField,
    IntField,
    DateField,
    DateTimeField,
    EmbeddedDocument,
    EmbeddedDocumentField)
from marshmallow import (
    Schema,
    fields,
    pre_load,
    post_load,
    EXCLUDE,
    validate,
    validates_schema,
    ValidationError)

from app.helpers.ma_schema_validators import not_blank, only_numbers


class SchoolContact(Document):
    name = StringField(required=True)
    email = EmailField(required=True)
    address = StringField(required=True)
    phone = StringField(required=True)
    schoolType = StringField(required=True, max_length=1)
    principalName = StringField(required=True)
    principalEmail = EmailField(required=True)
    principalPhone = StringField(required=True)
    subPrincipalName = StringField(required=True)
    subPrincipalEmail = EmailField(required=True)
    subPrincipalPhone = StringField(required=True)
    nTeachers = IntField(required=True)
    nAdministrativeStaff = IntField(required=True)
    nLaborStaff = IntField(required=True)
    nStudents = IntField(required=True)
    nGrades = IntField(required=True)
    nSections = IntField(required=True)
    schoolShift = StringField(required=True, max_length=1)
    hasSponsor = BooleanField(required=True)
    sponsorName = StringField()
    sponsorEmail = EmailField()
    sponsorAddress = StringField()
    sponsorPhone = StringField()
    sponsorCompanyType = StringField(max_length=1)
    state = StringField(required=True, default="1")
    status = BooleanField(default=True)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'schools_contacts'}

    def clean(self):
        self.updatedAt = datetime.utcnow()
    
"""
SCHEMAS
"""


class SchoolContactSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=not_blank)
    email = fields.Email(required=True)
    address = fields.Str(required=True, validate=not_blank)
    phone = fields.Str(required=True, validate=(not_blank, only_numbers))
    schoolType = fields.Str(
        required=True,
        validate=validate.OneOf(
            ('1','2','3'),
            ('national', 'statal', 'municipal')
        ))
    principalName = fields.Str(required=True)
    principalEmail = fields.Email(required=True)
    principalPhone = fields.Str(required=True, validate=only_numbers)
    subPrincipalName = fields.Str()
    subPrincipalEmail = fields.Email()
    subPrincipalPhone = fields.Str(validate=only_numbers)
    nTeachers = fields.Int(required=True,validate=validate.Range(min=0))
    nAdministrativeStaff = fields.Int(required=True,validate=validate.Range(min=0))
    nLaborStaff = fields.Int(required=True,validate=validate.Range(min=0))
    nStudents = fields.Int(required=True,validate=validate.Range(min=0))
    nGrades = fields.Int(required=True,validate=validate.Range(min=0))
    nSections = fields.Int(required=True,validate=validate.Range(min=0))
    schoolShift = fields.Str(
        required=True,
        validate=validate.OneOf(
            ('1','2','3'),
            ('morning', 'afternoon', 'both')
        ))
    hasSponsor = fields.Bool(required=True)
    sponsorName = fields.Str()
    sponsorEmail = fields.Email()
    sponsorAddress = fields.Str()
    sponsorPhone = fields.Str(validate=only_numbers)
    sponsorCompanyType = fields.Str(validate=validate.OneOf(
        ('1','2','3','4'),
        ('factory','grocery','personal business','other')
    ))
    state = fields.Str(
        default="1",
        validate=validate.OneOf(
            ('1','2','3'),
            ('pending', 'acepted', 'rejected')
        ))
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if 'name' in data:
            data["name"] = data["name"].title()
        if 'email' in data:
            data["email"] = data["email"].lower()
        if 'sponsorEmail' in data:
            data["sponsorEmail"] = data["sponsorEmail"].lower()
        return data

    @validates_schema
    def validate_schema(self, data, **kwargs):
        errors = {}
        if data['hasSponsor']:
            if 'sponsorName' not in data:
                errors["sponsorName"] = ["Field is required"]
            if 'sponsorEmail' not in data:
                errors["sponsorEmail"] = ["Field is required"]
            if 'sponsorAddress' not in data:
                errors["sponsorAddress"] = ["Field is required"]
            if 'sponsorPhone' not in data:
                errors["sponsorPhone"] = ["Field is required"]
            if 'sponsorCompanyType' not in data:
                errors["sponsorCompanyType"] = ["Field is required"]
        if errors:
            raise ValidationError(errors)
    
    class Meta:
        unknown = EXCLUDE
        ordered = True