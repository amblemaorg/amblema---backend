# app/models/yearbook_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields

from app.models.peca_activity_yearbook_model import ActivityYearbook


class Entity(EmbeddedDocument):
    name = fields.StringField()
    image = fields.URLField(null=True)
    content = fields.StringField()


class Yearbook(EmbeddedDocument):
    historicalReview = fields.EmbeddedDocumentField(ActivityYearbook)
    sponsor = fields.EmbeddedDocumentField(Entity)
    school = fields.EmbeddedDocumentField(Entity)
    coordinator = fields.EmbeddedDocumentField(Entity)
    isInApproval = fields.BooleanField(default=False)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
