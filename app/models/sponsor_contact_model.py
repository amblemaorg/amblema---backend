# /app/models/sponsor_contact_model.py


from datetime import datetime
import json

from mongoengine import (
    Document,
    EmbeddedDocument,
    fields)


class SponsorContact(Document):
    name = fields.StringField(required=True)
    email = fields.EmailField(required=True)
    rif = fields.StringField(required=True)
    companyType = fields.StringField(required=True)
    phone = fields.StringField(required=True)
    address = fields.StringField(required=True)
    addressState = fields.ReferenceField('State', required=True)
    addressMunicipality = fields.ReferenceField('Municipality', required=True)
    addressCity = fields.StringField(required=True)
    addressStreet = fields.StringField()
    contactName = fields.StringField(required=True)
    contactPhone = fields.StringField(required=True)
    schoolContact = fields.StringField(required=True, max_length=1)
    schoolContactName = fields.StringField(required=True)
    state = fields.StringField(required=True, default="1")
    status = fields.BooleanField(default=True)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'sponsors_contacts'}

    def clean(self):
        self.updatedAt = datetime.utcnow()
