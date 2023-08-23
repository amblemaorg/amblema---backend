# app/models/peca_annual_convention_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields

from app.models.shared_embedded_documents import CheckElement
from app.models.peca_activity_yearbook_model import ActivityYearbook


class AnnualConventionPeca(EmbeddedDocument):
    checklist = fields.EmbeddedDocumentListField(CheckElement)
    yearbook = fields.EmbeddedDocumentField(
        ActivityYearbook, default=ActivityYearbook())
    order = fields.IntField(default=100)
