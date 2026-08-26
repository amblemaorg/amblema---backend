# /app/models/sponsor_contact_model.py


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

from app.models.sponsor_user_model import SponsorUser
from app.models.school_user_model import SchoolUser
from app.models.user_model import User
from app.models.project_model import Project
from app.models.role_model import Role


class SponsorContact(Document):
    requestCode = fields.SequenceField(
        sequence_name="contact_requests", value_decorator=str)
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
    contactFirstName = fields.StringField()
    contactLastName = fields.StringField()
    contactEmail = fields.EmailField()
    contactPhone = fields.StringField()
    hasSchool = fields.BooleanField(required=True)
    hasSchoolRegistered = fields.BooleanField(default=False)
    school = fields.ReferenceField('SchoolUser', null=True)
    schoolName = fields.StringField()
    schoolCode = fields.StringField()
    schoolEmail = fields.EmailField()
    schoolAddress = fields.StringField()
    schoolAddressState = fields.ReferenceField('State')
    schoolAddressMunicipality = fields.ReferenceField('Municipality')
    schoolAddressCity = fields.StringField()
    schoolAddressZoneType = fields.StringField(max_length=1, null=True)
    schoolAddressZone = fields.StringField(null=True)
    schoolCoordinate = fields.PointField()
    schoolPhone = fields.StringField()
    schoolType = fields.StringField(max_length=1)
    schoolPrincipalFirstName = fields.StringField()
    schoolPrincipalLastName = fields.StringField()
    schoolPrincipalEmail = fields.EmailField()
    schoolPrincipalPhone = fields.StringField()
    schoolSubPrincipalFirstName = fields.StringField(null=True)
    schoolSubPrincipalLastName = fields.StringField(null=True)
    schoolSubPrincipalEmail = fields.EmailField(null=True)
    schoolSubPrincipalPhone = fields.StringField(null=True)
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
    def pre_save(cls, sender, document, **kwargs):
        if not document.id:
            email = document.email.lower().strip() if document.email else ""
            user = User.objects(
                isDeleted=False, email=email).first()
            if user:
                raise ValidationError(
                    {"email": [{"status": "5",
                                "msg": "Duplicated email"}]}
                )
            pendingRequest = SponsorContact.objects(
                isDeleted=False, email=email, status="1").first()
            if pendingRequest:
                raise ValidationError(
                    {"email": [{"status": "5",
                                "msg": "Duplicated pending request email"}]}
                )
            if document.hasSchool and not getattr(document, 'hasSchoolRegistered', False) and document.schoolCode:
                school = SchoolUser.objects(
                    isDeleted=False, code=document.schoolCode).first()
                if school:
                    raise ValidationError(
                        {"schoolCode": [{"status": "5",
                                         "msg": "Duplicated school code"}]}
                    )
                if document.schoolEmail:
                    user = User.objects(
                        isDeleted=False, email=document.schoolEmail).first()
                    if user:
                        raise ValidationError(
                            {"schoolEmail": [{"status": "5",
                                              "msg": "Duplicated school email"}]}
                        )
            if document.hasSchool and getattr(document, 'hasSchoolRegistered', False) and document.school:
                sc = document.school
                if not document.schoolName:
                    document.schoolName = sc.name
                if not document.schoolCode:
                    document.schoolCode = sc.code
                if not document.schoolEmail:
                    document.schoolEmail = sc.email
                if not document.schoolPhone:
                    document.schoolPhone = sc.phone
                if not document.schoolType:
                    document.schoolType = sc.schoolType
                if not document.schoolAddressState:
                    document.schoolAddressState = sc.addressState
                if not document.schoolAddressMunicipality:
                    document.schoolAddressMunicipality = sc.addressMunicipality
                if not document.schoolAddressCity:
                    document.schoolAddressCity = sc.addressCity
                if not document.schoolAddressZoneType:
                    document.schoolAddressZoneType = sc.addressZoneType
                if not document.schoolAddressZone:
                    document.schoolAddressZone = sc.addressZone
                if not document.schoolAddress:
                    document.schoolAddress = sc.address
                if not document.schoolCoordinate:
                    document.schoolCoordinate = sc.coordinate
                if not document.schoolPrincipalFirstName:
                    document.schoolPrincipalFirstName = sc.principalFirstName
                if not document.schoolPrincipalLastName:
                    document.schoolPrincipalLastName = sc.principalLastName
                if not document.schoolPrincipalEmail:
                    document.schoolPrincipalEmail = sc.principalEmail
                if not document.schoolPrincipalPhone:
                    document.schoolPrincipalPhone = sc.principalPhone
                if not document.schoolSubPrincipalFirstName:
                    document.schoolSubPrincipalFirstName = sc.subPrincipalFirstName
                if not document.schoolSubPrincipalLastName:
                    document.schoolSubPrincipalLastName = sc.subPrincipalLastName
                if not document.schoolSubPrincipalEmail:
                    document.schoolSubPrincipalEmail = sc.subPrincipalEmail
                if not document.schoolSubPrincipalPhone:
                    document.schoolSubPrincipalPhone = sc.subPrincipalPhone
                if not document.schoolNTeachers:
                    document.schoolNTeachers = sc.nTeachers
                if not document.schoolNAdministrativeStaff:
                    document.schoolNAdministrativeStaff = sc.nAdministrativeStaff
                if not document.schoolNLaborStaff:
                    document.schoolNLaborStaff = sc.nLaborStaff
                if not document.schoolNStudents:
                    document.schoolNStudents = sc.nStudents
                if not document.schoolNGrades:
                    document.schoolNGrades = sc.nGrades
                if not document.schoolNSections:
                    document.schoolNSections = sc.nSections
                if not document.schoolShift:
                    document.schoolShift = sc.schoolShift

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
                        contactEmail=document.contactEmail,
                        contactPhone=document.contactPhone
                    )
                    password = sponsorUser.generatePassword()
                    sponsorUser.password = password
                    sponsorUser.setHashPassword()
                    sponsorUser.save()
                    sponsorUser.sendRegistrationEmail(password)
                project.sponsor = sponsorUser

                if document.hasSchool:
                    if getattr(document, 'hasSchoolRegistered', False) and document.school:
                        schoolUser = document.school
                    else:
                        schoolUser = SchoolUser.objects.filter((
                            Q(email=document.schoolEmail) | Q(code=document.schoolCode)) & Q(isDeleted=False)).first() if (document.schoolEmail or document.schoolCode) else None
                        if not schoolUser and (document.schoolEmail or document.schoolCode):
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
                                addressZoneType=document.schoolAddressZoneType,
                                addressZone=document.schoolAddressZone,
                                address=document.schoolAddress,
                                coordinate=document.schoolCoordinate,
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
                    if schoolUser:
                        project.school = schoolUser
                project.save()


signals.pre_save_post_validation.connect(
    SponsorContact.post_save, sender=SponsorContact)
signals.pre_save.connect(
    SponsorContact.pre_save, sender=SponsorContact
)
