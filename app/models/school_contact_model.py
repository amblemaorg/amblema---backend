# /app/models/school_contact_model.py


from datetime import datetime
import json

from flask import current_app
from mongoengine import (
    Document,
    EmbeddedDocument,
    fields,
    signals,
    Q)
from marshmallow import ValidationError

from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.user_model import User
from app.models.project_model import Project
from app.models.role_model import Role


class SchoolContact(Document):
    requestCode = fields.SequenceField(
        sequence_name="contact_requests", value_decorator=str)
    name = fields.StringField(required=True)
    code = fields.StringField(required=True)
    email = fields.EmailField(required=True)
    address = fields.StringField()
    addressState = fields.ReferenceField('State', required=True)
    addressMunicipality = fields.ReferenceField('Municipality', required=True)
    addressCity = fields.StringField()
    addressZoneType = fields.StringField(max_length=1, null=True)
    addressZone = fields.StringField(null=True)
    coordinate = fields.PointField()
    phone = fields.StringField(required=True)
    schoolType = fields.StringField(required=True, max_length=1)
    principalFirstName = fields.StringField(required=True)
    principalLastName = fields.StringField(required=True)
    principalEmail = fields.EmailField(required=True)
    principalPhone = fields.StringField(required=True)
    subPrincipalFirstName = fields.StringField(null=True)
    subPrincipalLastName = fields.StringField(null=True)
    subPrincipalEmail = fields.EmailField(null=True)
    subPrincipalPhone = fields.StringField(null=True)
    nTeachers = fields.IntField(required=True)
    nAdministrativeStaff = fields.IntField(required=True)
    nLaborStaff = fields.IntField(required=True)
    nStudents = fields.IntField(required=True)
    nGrades = fields.IntField(required=True)
    nSections = fields.IntField(required=True)
    schoolShift = fields.StringField(required=True, max_length=1)
    hasSponsor = fields.BooleanField(required=True)
    hasSponsorRegistered = fields.BooleanField(default=False)
    sponsor = fields.ReferenceField('SponsorUser', null=True)
    sponsorName = fields.StringField()
    sponsorEmail = fields.EmailField()
    sponsorRif = fields.StringField()
    sponsorAddress = fields.StringField()
    sponsorAddressState = fields.ReferenceField('State')
    sponsorAddressMunicipality = fields.ReferenceField('Municipality')
    sponsorAddressCity = fields.StringField()
    sponsorCompanyType = fields.StringField()
    sponsorCompanyOtherType = fields.StringField()
    sponsorCompanyPhone = fields.StringField()
    sponsorContactFirstName = fields.StringField()
    sponsorContactLastName = fields.StringField()
    sponsorContactEmail = fields.EmailField()
    sponsorContactPhone = fields.StringField()
    status = fields.StringField(required=True, default="1")
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'schools_contacts'}

    def clean(self):
        self.updatedAt = datetime.utcnow()

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if not document.id:
            email = document.email.lower().strip() if document.email else ""
            school = SchoolUser.objects(
                isDeleted=False, code=document.code).first()
            if school:
                raise ValidationError(
                    {"code": [{"status": "5",
                               "msg": "Duplicated school code"}]}
                )
            user = User.objects(
                isDeleted=False, email=email).first()
            if user:
                raise ValidationError(
                    {"email": [{"status": "5",
                                "msg": "Duplicated school email"}]}
                )
            pendingRequest = SchoolContact.objects(
                isDeleted=False, email=email, status="1").first()
            if pendingRequest:
                raise ValidationError(
                    {"email": [{"status": "5",
                                "msg": "Duplicated pending request email"}]}
                )
            if document.hasSponsor and not getattr(document, 'hasSponsorRegistered', False) and document.sponsorEmail:
                user = User.objects(
                isDeleted=False, email=document.sponsorEmail).first()
                if user:
                    raise ValidationError(
                        {"sponsorEmail": [{"status": "5",
                                    "msg": "Duplicated sponsor email"}]}
                    )
            if document.hasSponsor and getattr(document, 'hasSponsorRegistered', False) and document.sponsor:
                sp = document.sponsor
                if not document.sponsorName:
                    document.sponsorName = sp.name
                if not document.sponsorEmail:
                    document.sponsorEmail = sp.email
                if not document.sponsorRif:
                    document.sponsorRif = sp.companyRif
                if not document.sponsorCompanyPhone:
                    document.sponsorCompanyPhone = sp.companyPhone
                if not document.sponsorCompanyType:
                    document.sponsorCompanyType = sp.companyType
                if not document.sponsorCompanyOtherType:
                    document.sponsorCompanyOtherType = sp.companyOtherType
                if not document.sponsorContactFirstName:
                    document.sponsorContactFirstName = sp.contactFirstName
                if not document.sponsorContactLastName:
                    document.sponsorContactLastName = sp.contactLastName
                if not document.sponsorContactEmail:
                    document.sponsorContactEmail = sp.contactEmail
                if not document.sponsorContactPhone:
                    document.sponsorContactPhone = sp.contactPhone
                if not document.sponsorAddressState:
                    document.sponsorAddressState = sp.addressState
                if not document.sponsorAddressMunicipality:
                    document.sponsorAddressMunicipality = sp.addressMunicipality
                if not document.sponsorAddressCity:
                    document.sponsorAddressCity = sp.addressCity
                if not document.sponsorAddress:
                    document.sponsorAddress = sp.address

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        if document.id:
            oldRequest = SchoolContact.objects.get(id=document.id)
            if document.status != oldRequest.status and document.status == '2':
                project = Project()
                schoolUser = SchoolUser.objects.filter(
                    (Q(email=document.email) | Q(code=document.code)) & Q(isDeleted=False)).first()
                if not schoolUser:
                    schoolUser = SchoolUser(
                        name=document.name,
                        email=document.email,
                        userType='4',
                        phone=document.phone,
                        role=Role.objects(
                            isDeleted=False, devName="school").first(),
                        addressState=document.addressState,
                        addressMunicipality=document.addressMunicipality,
                        addressCity=document.addressCity,
                        addressZoneType=document.addressZoneType,
                        addressZone=document.addressZone,
                        address=document.address,
                        coordinate=document.coordinate,
                        status='1',
                        code=document.code,
                        schoolType=document.schoolType,
                        principalFirstName=document.principalFirstName,
                        principalLastName=document.principalLastName,
                        principalEmail=document.principalEmail,
                        principalPhone=document.principalPhone,
                        subPrincipalFirstName=document.subPrincipalFirstName,
                        subPrincipalLastName=document.subPrincipalLastName,
                        subPrincipalEmail=document.subPrincipalEmail,
                        subPrincipalPhone=document.subPrincipalPhone,
                        nTeachers=document.nTeachers,
                        nAdministrativeStaff=document.nAdministrativeStaff,
                        nLaborStaff=document.nLaborStaff,
                        nStudents=document.nStudents,
                        nGrades=document.nGrades,
                        nSections=document.nSections,
                        schoolShift=document.schoolShift
                    )
                    password = schoolUser.generatePassword()
                    schoolUser.password = password
                    schoolUser.setHashPassword()
                    schoolUser.save()
                    schoolUser.sendRegistrationEmail(password)
                project.school = schoolUser

                if document.hasSponsor:
                    if getattr(document, 'hasSponsorRegistered', False) and document.sponsor:
                        sponsorUser = document.sponsor
                    else:
                        sponsorUser = SponsorUser.objects(
                            email=document.sponsorEmail).first() if document.sponsorEmail else None
                        if not sponsorUser and document.sponsorEmail:
                            sponsorUser = SponsorUser(
                                name=document.sponsorName,
                                email=document.sponsorEmail,
                                userType='3',
                                role=Role.objects(
                                    isDeleted=False, devName="sponsor").first(),
                                addressState=document.sponsorAddressState,
                                addressMunicipality=document.sponsorAddressMunicipality,
                                addressCity=document.sponsorAddressCity,
                                address=document.sponsorAddress,
                                status='1',
                                companyRif=document.sponsorRif,
                                companyType=document.sponsorCompanyType,
                                companyOtherType=document.sponsorCompanyOtherType,
                                companyPhone=document.sponsorCompanyPhone,
                                contactFirstName=document.sponsorContactFirstName,
                                contactLastName=document.sponsorContactLastName,
                                contactEmail=document.sponsorContactEmail,
                                contactPhone=document.sponsorContactPhone
                            )
                            password = sponsorUser.generatePassword()
                            sponsorUser.password = password
                            sponsorUser.setHashPassword()
                            sponsorUser.save()
                            sponsorUser.sendRegistrationEmail(password)
                    if sponsorUser:
                        project.sponsor = sponsorUser
                project.save()


signals.pre_save_post_validation.connect(
    SchoolContact.post_save, sender=SchoolContact)
signals.pre_save.connect(
    SchoolContact.pre_save, sender=SchoolContact)
