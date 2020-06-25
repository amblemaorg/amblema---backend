# app/models/yearbook_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields

from app.models.shared_embedded_documents import Approval


class Entity(EmbeddedDocument):
    name = fields.StringField()
    image = fields.StringField(null=True)
    content = fields.StringField()


class Yearbook(EmbeddedDocument):
    historicalReview = fields.EmbeddedDocumentField(Entity, default=Entity())
    sponsor = fields.EmbeddedDocumentField(Entity, default=Entity())
    school = fields.EmbeddedDocumentField(Entity, default=Entity())
    coordinator = fields.EmbeddedDocumentField(Entity, default=Entity())
    isInApproval = fields.BooleanField(default=False)
    approvalHistory = fields.EmbeddedDocumentListField(Approval)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
