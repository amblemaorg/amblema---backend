# app/models/shared_embedded_documents.py

from bson import ObjectId

from mongoengine import EmbeddedDocument, fields


class DocumentReference(EmbeddedDocument):
    id = fields.StringField(required=True)
    name = fields.StringField(required=True)


class ProjectReference(EmbeddedDocument):
    id = fields.StringField(required=True)
    code = fields.StringField(required=True)
    coordinator = fields.EmbeddedDocumentField(DocumentReference)
    sponsor = fields.EmbeddedDocumentField(DocumentReference)
    school = fields.EmbeddedDocumentField(DocumentReference)


class Link(EmbeddedDocument):
    name = fields.StringField()
    url = fields.URLField(required=True)


class CheckTemplate(EmbeddedDocument):
    id = fields.ObjectIdField(default=ObjectId())
    name = fields.StringField(required=True)
