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
from app.models.school_user_model import SchoolUser
from app.models.project_model import Project
from app.models.role_model import Role


class SponsorContact(Document):
    name = fields.StringField(required=True)
    email = fields.EmailField(required=True)
    rif = fields.StringField(required=True)
    companyType = fields.StringField(required=True)
    companyOtherType = fields.StringField()
    companyPhone = fields.StringField(required=True)
    address = fields.StringField()
    addressState = fields.ReferenceField('State', required=True)
    addressMunicipality = fields.ReferenceField('Municipality', required=True)
    addressCity = fields.StringField()
    addressStreet = fields.StringField()
    contactFirstName = fields.StringField()
    contactLastName = fields.StringField()
    contactPhone = fields.StringField()
    hasSchool = fields.BooleanField(required=True)
    schoolName = fields.StringField()
    schoolCode = fields.StringField()
    schoolEmail = fields.EmailField()
    schoolAddress = fields.StringField()
    schoolAddressState = fields.ReferenceField('State')
    schoolAddressMunicipality = fields.ReferenceField('Municipality')
    schoolAddressCity = fields.StringField()
    schoolAddressStreet = fields.StringField()
    schoolPhone = fields.StringField()
    schoolType = fields.StringField(max_length=1)
    schoolPrincipalFirstName = fields.StringField()
    schoolPrincipalLastName = fields.StringField()
    schoolPrincipalEmail = fields.EmailField()
    schoolPrincipalPhone = fields.StringField()
    schoolSubPrincipalFirstName = fields.StringField()
    schoolSubPrincipalLastName = fields.StringField()
    schoolSubPrincipalEmail = fields.EmailField()
    schoolSubPrincipalPhone = fields.StringField()
    schoolNTeachers = fields.IntField()
    schoolNAdministrativeStaff = fields.IntField()
    schoolNLaborStaff = fields.IntField()
    schoolNStudents = fields.IntField()
    schoolNGrades = fields.IntField()
    schoolNSections = fields.IntField()
    schoolShift = fields.StringField(max_length=1)
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
                        role=Role.objects(
                            isDeleted=False, devName="sponsor").first(),
                        addressState=document.addressState,
                        addressMunicipality=document.addressMunicipality,
                        addressCity=document.addressCity,
                        address=document.address,
                        status='1',
                        companyRif=document.rif,
                        companyType=document.companyType,
                        companyOtherType=document.companyOtherType,
                        companyPhone=document.companyPhone,
                        contactFirstName=document.contactFirstName,
                        contactLastName=document.contactLastName,
                        contactPhone=document.contactPhone
                    )
                    password = sponsorUser.generatePassword()
                    sponsorUser.password = password
                    sponsorUser.setHashPassword()
                    sponsorUser.save()
                    sponsorUser.sendRegistrationEmail(password)
                project.sponsor = sponsorUser

                if document.hasSchool:
                    schoolUser = SchoolUser.objects(
                        email=document.schoolEmail,
                        isDeleted=False).first()
                    if not schoolUser:
                        schoolUser = SchoolUser(
                            name=document.schoolName,
                            email=document.schoolEmail,
                            userType='4',
                            phone=document.schoolPhone,
                            role=Role.objects(
                                isDeleted=False, devName="school").first(),
                            addressState=document.schoolAddressState,
                            addressMunicipality=document.schoolAddressMunicipality,
                            addressCity=document.schoolAddressCity,
                            address=document.schoolAddress,
                            status='1',
                            code=document.schoolCode,
                            schoolType=document.schoolType,
                            principalFirstName=document.schoolPrincipalFirstName,
                            principalLastName=document.schoolPrincipalLastName,
                            principalEmail=document.schoolPrincipalEmail,
                            principalPhone=document.schoolPrincipalPhone,
                            subPrincipalFirstName=document.schoolSubPrincipalFirstName,
                            subPrincipalLastName=document.schoolSubPrincipalLastName,
                            subPrincipalEmail=document.schoolSubPrincipalEmail,
                            subPrincipalPhone=document.schoolSubPrincipalPhone,
                            nTeachers=document.schoolNTeachers,
                            nAdministrativeStaff=document.schoolNAdministrativeStaff,
                            nLaborStaff=document.schoolNLaborStaff,
                            nStudents=document.schoolNStudents,
                            nGrades=document.schoolNGrades,
                            nSections=document.schoolNSections,
                            schoolShift=document.schoolShift
                        )
                        password = schoolUser.generatePassword()
                        schoolUser.password = password
                        schoolUser.setHashPassword()
                        schoolUser.save()
                        schoolUser.sendRegistrationEmail(password)
                    project.school = schoolUser
                project.save()


signals.pre_save_post_validation.connect(
    SponsorContact.post_save, sender=SponsorContact)
