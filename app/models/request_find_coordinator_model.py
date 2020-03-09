# app/models/request_find_coordinator_model.py

from datetime import datetime

from flask import current_app
from mongoengine import Document, fields, signals

from app.models.project_model import Project
from app.models.coordinator_user_model import CoordinatorUser
from app.models.role_model import Role


class RequestFindCoordinator(Document):
    project = fields.ReferenceField(Project, required=True)
    firstName = fields.StringField(required=True)
    lastName = fields.StringField(required=True)
    cardType = fields.StringField(required=True)
    cardId = fields.StringField(required=True)
    birthdate = fields.DateTimeField(required=True)
    gender = fields.StringField(required=True, max_length=1)
    addressState = fields.ReferenceField('State', required=True)
    addressMunicipality = fields.ReferenceField('Municipality', required=True)
    addressCity = fields.StringField()
    addressStreet = fields.StringField()
    addressHome = fields.StringField()
    email = fields.EmailField(required=True)
    phone = fields.StringField(required=True)
    homePhone = fields.StringField(required=True)
    profession = fields.StringField()
    isReferred = fields.BooleanField(required=True)
    referredName = fields.StringField(required=True)
    status = fields.StringField(required=True, default="1")
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'requests_find_coordinator'}

    def clean(self):
        self.updatedAt = datetime.utcnow()

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if document.id:
            oldRequest = document.__class__.objects.get(id=document.id)
            if document.status != oldRequest.status and document.status == '2':
                coordinatorUser = CoordinatorUser.objects(
                    email=document.email).first()
                if not coordinatorUser:
                    coordinatorUser = CoordinatorUser(
                        name=document.firstName + ' ' + document.lastName,
                        email=document.email,
                        userType='2',
                        phone=document.phone,
                        role=Role.objects(isDeleted=False).first(),
                        addressState=document.addressState,
                        addressMunicipality=document.addressMunicipality,
                        addressCity=document.addressCity,
                        address="",
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
                        isReferred=document.isReferred,
                        referredName=document.referredName
                    )
                    password = coordinatorUser.generatePassword()
                    coordinatorUser.password = password
                    coordinatorUser.setHashPassword()
                    coordinatorUser.save()
                    coordinatorUser.sendRegistrationEmail(password)
                document.project.coordinator = coordinatorUser
                document.project.save()


signals.pre_save_post_validation.connect(
    RequestFindCoordinator.pre_save, sender=RequestFindCoordinator)
