# app/models/peca_activity_yearbook_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields


class ActivityYearbook(EmbeddedDocument):
    content = fields.StringField()
    images = fields.ListField(fields.URLField())
