# app/models/request_find_coordinator_model.py

from datetime import datetime

from flask import current_app
from mongoengine import Document, fields, signals
from marshmallow import ValidationError

from app.models.user_model import User
from app.models.project_model import Project, Approval
from app.models.coordinator_user_model import CoordinatorUser
from app.models.role_model import Role


class RequestFindCoordinator(Document):
    project = fields.ReferenceField(Project, required=True)
    user = fields.ReferenceField(User, required=True)
    requestCode = fields.SequenceField(
        sequence_name="find_requests", value_decorator=str)
    firstName = fields.StringField(required=True)
    lastName = fields.StringField(required=True)
    cardType = fields.StringField(required=True)
    cardId = fields.StringField(required=True)
    birthdate = fields.DateTimeField(required=True)
    gender = fields.StringField(required=True, max_length=1)
    addressState = fields.ReferenceField('State', required=True)
    addressMunicipality = fields.ReferenceField('Municipality', required=True)
    addressCity = fields.StringField()
    address = fields.StringField()
    addressHome = fields.StringField()
    email = fields.EmailField(required=True)
    phone = fields.StringField(required=True)
    homePhone = fields.StringField(required=True)
    profession = fields.StringField()
    status = fields.StringField(required=True, default="1")
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'requests_find_coordinator'}

    def clean(self):
        self.updatedAt = datetime.utcnow()

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if not document.id:
            user = User.objects(
                isDeleted=False, email=document.email).first()
            if user:
                raise ValidationError(
                    {"email": [{"status": "5",
                                "msg": "Duplicated email"}]}
                )

    @classmethod
    def pre_save_post_validation(cls, sender, document, **kwargs):
        reciprocalFields = [
            'sponsorFillCoordinatorForm',
            'schoolFillCoordinatorForm'
        ]
        # before update
        if document.id:
            oldRequest = document.__class__.objects.get(id=document.id)
            # is approved?
            if document.status != oldRequest.status and document.status == '2':
                coordinatorUser = CoordinatorUser.objects(
                    email=document.email).first()
                if not coordinatorUser:
                    coordinatorUser = CoordinatorUser(
                        name=document.firstName + ' ' + document.lastName,
                        email=document.email,
                        userType='2',
                        phone=document.phone,
                        role=Role.objects(
                            isDeleted=False, devName="coordinator").first(),
                        addressState=document.addressState,
                        addressMunicipality=document.addressMunicipality,
                        addressCity=document.addressCity,
                        address=document.address,
                        status='1',
                        firstName=document.firstName,
                        lastName=document.lastName,
                        cardType=document.cardType,
                        cardId=document.cardId,
                        gender=document.gender,
                        birthdate=document.birthdate,
                        homePhone=document.homePhone,
                        addressHome=document.addressHome,
                        profession=document.profession,
                        isReferred=True,
                        referredName=document.user.name
                    )
                    password = coordinatorUser.generatePassword()
                    coordinatorUser.password = password
                    coordinatorUser.setHashPassword()
                    coordinatorUser.save()
                    coordinatorUser.sendRegistrationEmail(password)
                document.project.coordinator = coordinatorUser
                for step in document.project.stepsProgress.steps:
                    if step.devName in reciprocalFields:
                        step.approve()  # approved
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
        from app.schemas.request_find_coordinator_schema import ReqFindCoordSchema
        # after create
        if 'created' in kwargs and kwargs['created']:
            reciprocalFields = [
                'sponsorFillCoordinatorForm',
                'schoolFillCoordinatorForm'
            ]
            for step in document.project.stepsProgress.steps:
                if step.devName in reciprocalFields:
                    step.status = "2"  # in approval
                    step.approvalHistory.append(
                        Approval(
                            id=str(document.id),
                            user=str(document.user.id),
                            data=ReqFindCoordSchema().dump(document),
                            status="1"
                        ))
            document.project.save()


signals.pre_save.connect(
    RequestFindCoordinator.pre_save, sender=RequestFindCoordinator)
signals.pre_save_post_validation.connect(
    RequestFindCoordinator.pre_save_post_validation, sender=RequestFindCoordinator)
signals.post_save.connect(
    RequestFindCoordinator.post_save, sender=RequestFindCoordinator)
