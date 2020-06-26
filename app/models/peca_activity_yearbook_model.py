# app/models/peca_activity_yearbook_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields


class ActivityYearbook(EmbeddedDocument):
    id = fields.StringField()
    name = fields.StringField()
    description = fields.StringField()
    images = fields.ListField(fields.StringField())
