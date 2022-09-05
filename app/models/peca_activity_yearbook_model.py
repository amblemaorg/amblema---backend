# app/models/peca_activity_yearbook_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields

class PrintOption(EmbeddedDocument):
    print = fields.BooleanField(default=True)
    expandGallery = fields.BooleanField(default=True)
class ActivityYearbook(EmbeddedDocument):
    id = fields.StringField()
    name = fields.StringField()
    description = fields.StringField(null=True)
    images = fields.ListField(fields.StringField())
    printOption = fields.EmbeddedDocumentField(PrintOption, default=PrintOption())
