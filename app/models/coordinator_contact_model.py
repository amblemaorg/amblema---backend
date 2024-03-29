# /app/models/coordinator_contact_model.py


from datetime import datetime
import json

from flask import current_app
from mongoengine import (
    Document,
    EmbeddedDocument,
    fields,
    signals)
from app.models.coordinator_user_model import CoordinatorUser
from app.models.project_model import Project
from app.models.role_model import Role
from app.models.user_model import User
from marshmallow import ValidationError


class CoordinatorContact(Document):
    requestCode = fields.SequenceField(
        sequence_name="contact_requests", value_decorator=str)
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
    profession = fields.StringField(required=True)
    isReferred = fields.BooleanField(required=True)
    referredName = fields.StringField()
    status = fields.StringField(required=True, default="1")
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'coordinators_contacts'}

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
    def post_save(cls, sender, document, **kwargs):
        if document.id:
            oldRequest = CoordinatorContact.objects.get(id=document.id)
            if document.status != oldRequest.status and document.status == '2':
                project = Project()
                coordinatorUser = CoordinatorUser.objects(
                    email=document.email).first()
                if not coordinatorUser:
                    coordinatorUser = CoordinatorUser(
                        name=document.firstName + ' ' + document.lastName,
                        email=document.email,
                        userType='2',
                        phone=document.phone,
                        address = document.address,
                        role=Role.objects(
                            isDeleted=False, devName="coordinator").first(),
                        addressState=document.addressState,
                        addressMunicipality=document.addressMunicipality,
                        addressCity=document.addressCity,
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
                project.coordinator = coordinatorUser
                project.save()


signals.pre_save_post_validation.connect(
    CoordinatorContact.post_save, sender=CoordinatorContact)
signals.pre_save.connect(
    CoordinatorContact.pre_save, sender=CoordinatorContact)
