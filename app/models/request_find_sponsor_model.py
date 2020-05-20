# app/models/request_find_sponsor_model.py

from datetime import datetime

from flask import current_app
from mongoengine import Document, fields, signals

from app.models.user_model import User
from app.models.project_model import Project, Approval
from app.models.sponsor_user_model import SponsorUser
from app.models.role_model import Role


class RequestFindSponsor(Document):
    project = fields.ReferenceField(Project, required=True)
    user = fields.ReferenceField(User, required=True)
    requestCode = fields.SequenceField(
        sequence_name="find_requests", value_decorator=str)
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
    status = fields.StringField(required=True, default="1")
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'requests_find_sponsor'}

    def clean(self):
        self.updatedAt = datetime.utcnow()

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        reciprocalFields = [
            'coordinatorFillSponsorForm',
            'schoolFillSponsorForm'
        ]
        # before update
        if document.id:
            oldRequest = document.__class__.objects.get(id=document.id)
            # is approved?
            if document.status != oldRequest.status and document.status == '2':
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
                document.project.sponsor = sponsorUser
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
        from app.schemas.request_find_sponsor_schema import ReqFindSponsorSchema
        # after create
        if 'created' in kwargs and kwargs['created']:
            reciprocalFields = [
                'coordinatorFillSponsorForm',
                'schoolFillSponsorForm'
            ]
            for step in document.project.stepsProgress.steps:
                if step.devName in reciprocalFields:
                    step.status = "2"  # in approval
                    step.approvalHistory.append(
                        Approval(
                            id=str(document.id),
                            user=str(document.user.id),
                            data=ReqFindSponsorSchema().dump(document),
                            status="1"
                        ))
            document.project.save()


signals.pre_save_post_validation.connect(
    RequestFindSponsor.pre_save, sender=RequestFindSponsor)

signals.post_save.connect(
    RequestFindSponsor.post_save, sender=RequestFindSponsor)
