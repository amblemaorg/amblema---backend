# app/models/find_school.py

from datetime import datetime

from flask import current_app
from mongoengine import fields, Document, signals

from app.models.project_model import Project
from app.models.school_user_model import SchoolUser
from app.models.role_model import Role


class RequestFindSchool(Document):
    project = fields.ReferenceField(Project, required=True)
    name = fields.StringField(required=True)
    code = fields.StringField(required=True)
    email = fields.EmailField(required=True)
    address = fields.StringField()
    addressState = fields.ReferenceField('State', required=True)
    addressMunicipality = fields.ReferenceField('Municipality', required=True)
    addressCity = fields.StringField()
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
    status = fields.StringField(required=True, default="1")
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'requests_find_school'}

    def clean(self):
        self.updatedAt = datetime.utcnow()

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if document.id:
            oldRequest = document.__class__.objects.get(id=document.id)
            if document.status != oldRequest.status and document.status == '2':
                schoolUser = SchoolUser.objects(email=document.email).first()
                if not schoolUser:
                    schoolUser = SchoolUser(
                        name=document.name,
                        email=document.email,
                        userType='4',
                        phone=document.phone,
                        role=Role.objects(isDeleted=False).first(),
                        addressState=document.addressState,
                        addressMunicipality=document.addressMunicipality,
                        addressCity=document.addressCity,
                        address=document.address,
                        status='1',
                        code=document.code,
                        contactFirstName=document.principalFirstName,
                        contactLastName=document.principalLastName,
                        contactEmail=document.principalEmail,
                        contactPhone=document.principalPhone,
                        contactFunction="Director",
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
                document.project.school = schoolUser
                document.project.save()


signals.pre_save_post_validation.connect(
    RequestFindSchool.pre_save, sender=RequestFindSchool)
