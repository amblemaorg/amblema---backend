# /app/models/sponsor_contact_model.py


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


class SponsorContact(Document):
    name = StringField(required=True)
    email = EmailField(required=True)
    address = StringField(required=True)
    contactName = StringField(required=True)
    contactPhone = StringField(required=True)
    schoolContact = StringField(required=True, max_length=1)
    schoolContactName = StringField(required=True)
    state = StringField(required=True, default="1")
    status = BooleanField(default=True)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'sponsors_contacts'}

    def clean(self):
        self.updatedAt = datetime.utcnow()
    
"""
SCHEMAS
"""


class SponsorContactSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=not_blank)
    email = fields.Email(required=True, validate=not_blank)
    address = fields.Str(required=True, validate=not_blank)
    contactName = fields.Str(required=True, validate=not_blank)
    contactPhone = fields.Str(required=True, validate=not_blank)
    schoolContact = fields.Str(
        required=True,
        validate=validate.OneOf(
            ('1','2','3','4'),
            ('director','teacher','parent','neighbor')
        ))
    schoolContactName = fields.Str(required=True, validate=not_blank)
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
        return data
    
    class Meta:
        unknown = EXCLUDE
        ordered = True