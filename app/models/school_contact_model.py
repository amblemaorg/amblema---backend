# /app/models/school_contact_model.py


from datetime import datetime
import json

from mongoengine import (
    Document,
    EmbeddedDocument,
    fields)


class SchoolContact(Document):
    name = fields.StringField(required=True)
    code = fields.StringField(required=True)
    email = fields.EmailField(required=True)
    address = fields.StringField(required=True)
    addressState = fields.ReferenceField('State', required=True)
    addressMunicipality = fields.ReferenceField('Municipality', required=True)
    addressCity = fields.StringField(required=True)
    addressStreet = fields.StringField()
    phone = fields.StringField(required=True)
    schoolType = fields.StringField(required=True, max_length=1)
    principalFirstName = fields.StringField(required=True)
    principalLastName = fields.StringField(required=True)
    principalEmail = fields.EmailField(required=True)
    principalPhone = fields.StringField(required=True)
    subPrincipalFirstName = fields.StringField(required=True)
    subPrincipalLastName = fields.StringField(required=True)
    subPrincipalEmail = fields.EmailField(required=True)
    subPrincipalPhone = fields.StringField(required=True)
    nTeachers = fields.IntField(required=True)
    nAdministrativeStaff = fields.IntField(required=True)
    nLaborStaff = fields.IntField(required=True)
    nStudents = fields.IntField(required=True)
    nGrades = fields.IntField(required=True)
    nSections = fields.IntField(required=True)
    schoolShift = fields.StringField(required=True, max_length=1)
    hasSponsor = fields.BooleanField(required=True)
    sponsorName = fields.StringField()
    sponsorEmail = fields.EmailField()
    sponsorRIF = fields.StringField()
    sponsorAddress = fields.StringField()
    sponsorAddressState = fields.ReferenceField('State')
    sponsorAddressMunicipality = fields.ReferenceField('Municipality')
    sponsorAddressCity = fields.StringField()
    sponsorAddressStreet = fields.StringField()
    sponsorPhone = fields.StringField()
    sponsorCompanyType = fields.StringField()
    sponsorContactFirstName = fields.StringField()
    sponsorContactLastName = fields.StringField()
    sponsorContactPhone = fields.StringField()
    state = fields.StringField(required=True, default="1")
    status = fields.BooleanField(default=True)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'schools_contacts'}

    def clean(self):
        self.updatedAt = datetime.utcnow()
