# app/models/peca_olympics_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields

from app.models.shared_embedded_documents import Link
from app.models.peca_activity_yearbook_model import ActivityYearbook


class Section(EmbeddedDocument):
    id = fields.StringField(required=True)
    name = fields.StringField(required=True)
    grade = fields.StringField()


class Student(EmbeddedDocument):
    id = fields.StringField()
    name = fields.StringField()
    section = fields.EmbeddedDocumentField(Section)
    status = fields.StringField(default="1")
    result = fields.StringField(null=True)


class Olympics(EmbeddedDocument):
    students = fields.EmbeddedDocumentListField(Student)
    file = fields.EmbeddedDocumentField(Link)
    description = fields.StringField()
    yearbook = fields.EmbeddedDocumentField(ActivityYearbook)
