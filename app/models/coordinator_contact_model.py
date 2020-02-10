# /app/models/coordinator_contact_model.py


from datetime import datetime
import json

from mongoengine import (
    Document,
    EmbeddedDocument,
    fields)


class CoordinatorContact(Document):
    firstName = fields.StringField(required=True)
    lastName = fields.StringField(required=True)
    cardType = fields.StringField(required=True)
    cardId = fields.StringField(required=True)
    birthDate = fields.DateField(required=True)
    gender = fields.StringField(required=True, max_length=1)
    addressState = fields.ReferenceField('State', required=True)
    addressMunicipality = fields.ReferenceField('Municipality', required=True)
    addressCity = fields.StringField(required=True)
    addressStreet = fields.StringField()
    addressHome = fields.StringField()
    email = fields.EmailField(required=True)
    phone = fields.StringField(required=True)
    homePhone = fields.StringField()
    profession = fields.StringField(required=True)
    referredName = fields.StringField(required=True)
    state = fields.StringField(required=True, default="1")
    status = fields.BooleanField(default=True)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'coordinators_contacts'}

    def clean(self):
        self.updatedAt = datetime.utcnow()
