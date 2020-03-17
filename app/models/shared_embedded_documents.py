# app/models/shared_embedded_documents.py


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
