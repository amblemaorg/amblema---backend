# app/models/shared_embedded_documents.py


from mongoengine import EmbeddedDocument, StringField, EmbeddedDocumentField


class DocumentReference(EmbeddedDocument):
    id = StringField(required=True)
    name = StringField(required=True)


class ProjectReference(EmbeddedDocument):
    id = StringField(required=True)
    code = StringField(required=True)
    coordinator = EmbeddedDocumentField(DocumentReference)
    sponsor = EmbeddedDocumentField(DocumentReference)
    school = EmbeddedDocumentField(DocumentReference)
