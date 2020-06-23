# app/models/peca_annual_preparation_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields
from app.models.peca_activity_yearbook_model import ActivityYearbook


class Teacher(EmbeddedDocument):
    id = fields.StringField()
    firstName = fields.StringField()
    lastName = fields.StringField()
    phone = fields.StringField()
    email = fields.StringField()
    annualPreparationStatus = fields.StringField(max_length=1, default="1")
    pecaId = fields.StringField()


class AnnualPreparationPeca(EmbeddedDocument):
    step1Description = fields.StringField()
    step2Description = fields.StringField()
    step3Description = fields.StringField()
    step4Description = fields.StringField()
    teachers = fields.EmbeddedDocumentListField(Teacher)
