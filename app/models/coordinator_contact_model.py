# /app/models/coordinator_contact_model.py


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


class CoordinatorContact(Document):
    firstName = StringField(required=True)
    lastName = StringField(required=True)
    birthDate = DateField(required=True)
    gender = StringField(required=True, max_length=1)
    city = StringField(required=True)
    email = EmailField(required=True)
    phone = StringField(required=True)
    profession = StringField(required=True)
    referredName = StringField(required=True)
    state = StringField(required=True, default="1")
    status = BooleanField(default=True)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'coordinators_contacts'}

    def clean(self):
        self.updatedAt = datetime.utcnow()
    
"""
SCHEMAS
"""


class CoordinatorContactSchema(Schema):
    id = fields.Str(dump_only=True)
    firstName = fields.Str(required=True, validate=not_blank)
    lastName = fields.Str(required=True, validate=not_blank)
    birthDate = fields.Date(required=True)
    gender = fields.Str(
        required=True,
        validate=validate.OneOf(
            ('1','2'),
            ('female','male')
        ))
    city = fields.Str(required=True, validate=not_blank)
    email = fields.Email(required=True, validate=not_blank)
    phone = fields.Str(required=True, validate=(not_blank, only_numbers))
    profession = fields.Str(required=True, validate=not_blank)
    referredName = fields.Str(required=True, validate=not_blank)
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
        if 'firstName' in data:
            data["firstName"] = data["firstName"].title()
        if 'lastName' in data:
            data["lastName"] = data["lastName"].title()
        if 'email' in data:
            data["email"] = data["email"].lower()
        return data
    
    class Meta:
        unknown = EXCLUDE
        ordered = True