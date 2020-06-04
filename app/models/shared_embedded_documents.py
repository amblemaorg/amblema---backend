# app/models/shared_embedded_documents.py

from datetime import datetime

from mongoengine import EmbeddedDocument, fields


class DocumentReference(EmbeddedDocument):
    id = fields.StringField()
    name = fields.StringField()


class SchoolReference(EmbeddedDocument):
    id = fields.StringField()
    name = fields.StringField()
    code = fields.StringField()


class ProjectReference(EmbeddedDocument):
    id = fields.StringField(required=True)
    code = fields.StringField(required=True)
    coordinator = fields.EmbeddedDocumentField(DocumentReference)
    sponsor = fields.EmbeddedDocumentField(DocumentReference)
    school = fields.EmbeddedDocumentField(SchoolReference)


class Link(EmbeddedDocument):
    name = fields.StringField()
    url = fields.URLField(required=True)


class CheckTemplate(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    name = fields.StringField(required=True)


class ImageStatus(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    pecaId = fields.StringField()
    image = fields.URLField()
    description = fields.StringField()
    approvalStatus = fields.StringField(default="1", max_length=1)
    visibilityStatus = fields.StringField(default="2", max_length=1)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
