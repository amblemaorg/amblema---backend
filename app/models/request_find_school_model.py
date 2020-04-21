# app/models/find_school.py

from datetime import datetime

from flask import current_app
from mongoengine import fields, Document, signals

from app.models.user_model import User
from app.models.project_model import Project, Approval
from app.models.school_user_model import SchoolUser
from app.models.role_model import Role


class RequestFindSchool(Document):
    project = fields.ReferenceField(Project, required=True)
    user = fields.ReferenceField(User, required=True)
    requestCode = fields.SequenceField(
        sequence_name="find_requests", value_decorator=str)
    name = fields.StringField(required=True)
    code = fields.StringField(required=True)
    email = fields.EmailField(required=True)
    address = fields.StringField()
    addressState = fields.ReferenceField('State', required=True)
    addressMunicipality = fields.ReferenceField('Municipality', required=True)
    addressCity = fields.StringField()
    addressZoneType = fields.StringField(max_length=1, null=True)
    addressZone = fields.StringField(null=True)
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
    status = fields.StringField(required=True, default="1")
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'requests_find_school'}

    def clean(self):
        self.updatedAt = datetime.utcnow()

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        reciprocalFields = [
            'coordinatorFillSchoolForm',
            'sponsorFillSchoolForm'
        ]
        # before update
        if document.id:
            oldRequest = document.__class__.objects.get(id=document.id)
            # is approved?
            if document.status != oldRequest.status and document.status == '2':
                schoolUser = SchoolUser.objects(email=document.email).first()
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
                document.project.school = schoolUser
                for step in document.project.stepsProgress.steps:
                    if step.devName in reciprocalFields:
                        step.status = "2"  # approved
                        for approval in step.approvalHistory:
                            if approval.id == str(document.id):
                                approval.status = document.status
                                approval.updatedAt = datetime.utcnow()
                document.project.save()
            # is rejected?
            if document.status != oldRequest.status and document.status == '3':
                for step in document.project.stepsProgress.steps:
                    if step.devName in reciprocalFields:
                        step.status = "1"  # pending
                        for approval in step.approvalHistory:
                            if approval.id == str(document.id):
                                approval.status = document.status
                                approval.updatedAt = datetime.utcnow()
                document.project.save()

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        from app.schemas.request_find_school_schema import ReqFindSchoolSchema
        # after create
        reciprocalFields = [
            'coordinatorFillSchoolForm',
            'sponsorFillSchoolForm'
        ]
        for step in document.project.stepsProgress.steps:
            if step.devName in reciprocalFields:
                step.status = "2"  # in approval
                step.approvalHistory.append(
                    Approval(
                        id=str(document.id),
                        data=ReqFindSchoolSchema().dump(document),
                        status="1"
                    ))
        document.project.save()


signals.pre_save_post_validation.connect(
    RequestFindSchool.pre_save, sender=RequestFindSchool)

signals.post_save.connect(
    RequestFindSchool.post_save, sender=RequestFindSchool)
