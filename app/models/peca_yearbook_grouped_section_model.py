# app/models/peca_yearbook_grouped_section_model.py

from mongoengine import Document, fields
from app.models.peca_project_model import PecaProject

class PecaYearbookGroupedSection(Document):
    pecaId = fields.ReferenceField(PecaProject)
    sectionId = fields.StringField(required=True)
    groupedWith = fields.StringField(required=True)
