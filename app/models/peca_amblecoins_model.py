# app/models/peca_amblecoins_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields


class AmbleSection(EmbeddedDocument):
    id = fields.StringField()
    name = fields.StringField()
    grade = fields.StringField()
    status = fields.StringField(default="1")


class AmblecoinsPeca(EmbeddedDocument):
    meetingDate = fields.DateTimeField()
    elaborationDate = fields.DateTimeField()
    sections = fields.EmbeddedDocumentListField(AmbleSection)
