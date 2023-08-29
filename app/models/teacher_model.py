# app/models/teacher_model.py


from datetime import datetime

from flask import current_app
from mongoengine import EmbeddedDocument, fields


class Teacher(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    firstName = fields.StringField()
    lastName = fields.StringField()
    cardType = fields.StringField(max_length=1)
    cardId = fields.StringField()
    gender = fields.StringField(max_length=1)
    email = fields.StringField()
    phone = fields.StringField()
    addressState = fields.ReferenceField('State')
    addressMunicipality = fields.ReferenceField('Municipality')
    address = fields.StringField()
    addressCity = fields.StringField()
    specialty = fields.ReferenceField('SpecialtyTeacher')
    workPosition = fields.ReferenceField('WorkPosition')
    status = fields.StringField(max_length=1, default="1")
    #annualPreparationStatus = fields.StringField(max_length=1, null=True)
    pecaId = fields.StringField()
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
