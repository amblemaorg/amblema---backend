# app/models/activity_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields
from app.models.shared_embedded_documents import Link, CheckTemplate


class Activity(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    name = fields.StringField()
    devName = fields.StringField()
    hasText = fields.BooleanField(required=True, default=False)
    hasDate = fields.BooleanField(required=True, default=False)
    hasFile = fields.BooleanField(required=True, default=False)
    hasVideo = fields.BooleanField(required=True, default=False)
    hasChecklist = fields.BooleanField(required=True, default=False)
    hasUpload = fields.BooleanField(required=True, default=False)
    text = fields.StringField()
    file = fields.EmbeddedDocumentField(
        Link, is_file=True, null=True, default=None)
    video = fields.EmbeddedDocumentField(Link, null=True, default=None)
    checklist = fields.EmbeddedDocumentListField(
        CheckTemplate, null=True, default=None)
    approvalType = fields.StringField(required=True, max_length=1)
    status = fields.StringField(default='2', max_length=1)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
