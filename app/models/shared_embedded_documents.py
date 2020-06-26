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
    id = fields.StringField()
    code = fields.StringField()
    coordinator = fields.EmbeddedDocumentField(DocumentReference)
    sponsor = fields.EmbeddedDocumentField(DocumentReference)
    school = fields.EmbeddedDocumentField(SchoolReference)


class Link(EmbeddedDocument):
    name = fields.StringField()
    url = fields.StringField(required=True)


class CheckTemplate(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    name = fields.StringField(required=True)


class Approval(EmbeddedDocument):
    id = fields.StringField()
    user = fields.ReferenceField('User')
    comments = fields.StringField()
    detail = fields.DictField()
    status = fields.StringField(max_length=1, default="1")
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)


class ImageStatus(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    schoolId = fields.StringField()
    image = fields.StringField()
    description = fields.StringField()
    approvalStatus = fields.StringField(default="1", max_length=1)
    visibilityStatus = fields.StringField(default="2", max_length=1)
    approvalHistory = fields.EmbeddedDocumentField(Approval)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)


class Coordinate(EmbeddedDocument):
    latitude = fields.FloatField()
    longitude = fields.FloatField()
