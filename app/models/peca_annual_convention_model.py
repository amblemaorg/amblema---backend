# app/models/peca_annual_convention_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields

from app.models.project_model import CheckElement


class AnnualConventionPeca(EmbeddedDocument):
    checklist = fields.EmbeddedDocumentListField(CheckElement)
