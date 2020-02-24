# /app/models/sponsor_contact_model.py


from datetime import datetime
import json

from flask import current_app
from mongoengine import (
    Document,
    EmbeddedDocument,
    fields,
    signals)

from app.models.sponsor_user_model import SponsorUser
from app.models.project_model import Project
from app.models.role_model import Role


class SponsorContact(Document):
    name = fields.StringField(required=True)
    email = fields.EmailField(required=True)
    rif = fields.StringField(required=True)
    companyType = fields.StringField(required=True)
    companyOtherType = fields.StringField()
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
    status = fields.StringField(required=True, default="1")
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'sponsors_contacts'}

    def clean(self):
        self.updatedAt = datetime.utcnow()

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        if document.id:
            oldRequest = SponsorContact.objects.get(id=document.id)
            if document.status != oldRequest.status and document.status == '2':
                project = Project()
                sponsorUser = SponsorUser.objects(
                    email=document.email).first()
                if not sponsorUser:
                    sponsorUser = SponsorUser(
                        name=document.name,
                        email=document.email,
                        userType='3',
                        phone=document.phone,
                        role=Role.objects(isDeleted=False).first(),
                        addressState=document.addressState,
                        addressMunicipality=document.addressMunicipality,
                        addressCity=document.addressCity,
                        address=document.address,
                        status='1',
                        firstName=document.contactName,
                        lastName="",
                        cardType="2",
                        cardId=document.rif,
                        companyRIF=document.rif,
                        companyType=document.companyType,
                        companyOtherType=document.companyOtherType,
                        companyPhone=document.phone,
                        contactName=document.contactName,
                        contactPhone=document.contactPhone
                    )
                    password = sponsorUser.generatePassword()
                    sponsorUser.password = password
                    sponsorUser.setHashPassword()
                    sponsorUser.save()
                    sponsorUser.sendRegistrationEmail(password)
                project.sponsor = sponsorUser
                project.save()


signals.pre_save_post_validation.connect(
    SponsorContact.post_save, sender=SponsorContact)
