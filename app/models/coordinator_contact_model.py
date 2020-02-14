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


class CoordinatorContact(Document):
    firstName = fields.StringField(required=True)
    lastName = fields.StringField(required=True)
    cardType = fields.StringField(required=True)
    cardId = fields.StringField(required=True)
    birthdate = fields.DateField(required=True)
    gender = fields.StringField(required=True, max_length=1)
    addressState = fields.ReferenceField('State', required=True)
    addressMunicipality = fields.ReferenceField('Municipality', required=True)
    addressCity = fields.StringField(required=True)
    addressStreet = fields.StringField()
    addressHome = fields.StringField()
    email = fields.EmailField(required=True)
    phone = fields.StringField(required=True)
    homePhone = fields.StringField(required=True)
    profession = fields.StringField(required=True)
    referredName = fields.StringField(required=True)
    state = fields.StringField(required=True, default="1")
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'coordinators_contacts'}

    def clean(self):
        self.updatedAt = datetime.utcnow()

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        current_app.logger.info('*** CoordinatorContact post_save ***')
        if document.id:
            current_app.logger.info('*** post_update ***')
            oldRequest = CoordinatorContact.objects.get(id=document.id)
            current_app.logger.info('*** post update***')
            if document.state != oldRequest.state and document.state == '2':
                current_app.logger.info('***state=2***')
                project = Project()
                coordinatorUser = CoordinatorUser.objects(
                    email=document.email).first()
                if not coordinatorUser:
                    coordinatorUser = CoordinatorUser(
                        name=document.firstName + ' ' + document.lastName,
                        email=document.email,
                        userType='2',
                        phone=document.phone,
                        role=Role.objects(status=True).first(),
                        addressState=document.addressState,
                        addressMunicipality=document.addressMunicipality,
                        addressCity=document.addressCity,
                        address="",
                        state='1',
                        firstName=document.firstName,
                        lastName=document.lastName,
                        cardType=document.cardType,
                        cardId=document.cardId,
                        birthdate=document.birthdate,
                        homePhone=document.homePhone,
                        addressHome=document.addressHome
                    )
                    current_app.logger.info('homePhone')
                    current_app.logger.info(coordinatorUser.homePhone)
                    password = coordinatorUser.generatePassword()
                    coordinatorUser.password = password
                    coordinatorUser.setHashPassword()
                    coordinatorUser.save()
                    coordinatorUser.sendRegistrationEmail(password)
                project.coordinator = coordinatorUser
                project.save()


signals.pre_save_post_validation.connect(
    CoordinatorContact.post_save, sender=CoordinatorContact)
