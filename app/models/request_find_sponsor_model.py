# app/models/request_find_sponsor_model.py

from datetime import datetime

from flask import current_app
from mongoengine import Document, fields, signals

from app.models.project_model import Project
from app.models.sponsor_user_model import SponsorUser
from app.models.role_model import Role


class RequestFindSponsor(Document):
    project = fields.ReferenceField(Project, required=True)
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
    contactFirstName = fields.StringField()
    contactLastName = fields.StringField()
    contactPhone = fields.StringField(required=True)
    status = fields.StringField(required=True, default="1")
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'requests_find_sponsor'}

    def clean(self):
        self.updatedAt = datetime.utcnow()

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if document.id:
            oldRequest = document.__class__.objects.get(id=document.id)
            if document.status != oldRequest.status and document.status == '2':
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
                        companyRIF=document.rif,
                        companyType=document.companyType,
                        companyOtherType=document.companyOtherType,
                        companyPhone=document.phone,
                        contactFirstName=document.contactFirstName,
                        contactLastName=document.contactLastName,
                        contactPhone=document.contactPhone
                    )
                    password = sponsorUser.generatePassword()
                    sponsorUser.password = password
                    sponsorUser.setHashPassword()
                    sponsorUser.save()
                    sponsorUser.sendRegistrationEmail(password)
                document.project.sponsor = sponsorUser
                document.project.save()


signals.pre_save_post_validation.connect(
    RequestFindSponsor.pre_save, sender=RequestFindSponsor)
