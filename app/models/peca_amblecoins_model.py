# app/models/peca_amblecoins_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields
from app.models.peca_activity_yearbook_model import ActivityYearbook
from app.models.learning_module_model import Image
from app.models.shared_embedded_documents import Link


class AmbleSection(EmbeddedDocument):
    id = fields.StringField()
    name = fields.StringField()
    grade = fields.StringField()
    status = fields.StringField(default="1")


class AmblecoinsPeca(EmbeddedDocument):
    teachersMeetingFile = fields.EmbeddedDocumentField(
        Link, is_file=True)
    teachersMeetingDescription = fields.StringField()
    piggyBankDescription = fields.StringField()
    piggyBankSlider = fields.EmbeddedDocumentListField(Image)
    meetingDate = fields.DateTimeField()
    elaborationDate = fields.DateTimeField()
    sections = fields.EmbeddedDocumentListField(AmbleSection)
    yearbook = fields.EmbeddedDocumentField(
        ActivityYearbook, default=ActivityYearbook())
    order = fields.IntField(default=100)

