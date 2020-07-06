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


class ResumeSchoolYear(EmbeddedDocument):
    id = fields.StringField()
    name = fields.StringField()
    status = fields.StringField(max_length=1)


class ResumePeca(EmbeddedDocument):
    pecaId = fields.StringField()
    schoolYear = fields.EmbeddedDocumentField(ResumeSchoolYear)
    createAt = fields.DateTimeField(default=datetime.utcnow)


class ProjectReference(EmbeddedDocument):
    id = fields.StringField()
    code = fields.StringField()
    coordinator = fields.EmbeddedDocumentField(DocumentReference)
    sponsor = fields.EmbeddedDocumentField(DocumentReference)
    school = fields.EmbeddedDocumentField(SchoolReference)
    schoolYears = fields.EmbeddedDocumentListField(ResumePeca)


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
    image = fields.StringField()
    description = fields.StringField()


class Coordinate(EmbeddedDocument):
    latitude = fields.FloatField()
    longitude = fields.FloatField()


class DiagnosticSummary(EmbeddedDocument):
    wordsPerMin = fields.IntField(default=0)
    wordsPerMinIndex = fields.FloatField(default=0)
    multiplicationsPerMin = fields.IntField(default=0)
    multiplicationsPerMinIndex = fields.FloatField(default=0)
    operationsPerMin = fields.IntField(default=0)
    operationsPerMinIndex = fields.FloatField(default=0)


class Diagnostics(EmbeddedDocument):
    lapse1 = fields.EmbeddedDocumentField(
        DiagnosticSummary, default=DiagnosticSummary())
    lapse2 = fields.EmbeddedDocumentField(
        DiagnosticSummary, default=DiagnosticSummary())
    lapse3 = fields.EmbeddedDocumentField(
        DiagnosticSummary, default=DiagnosticSummary())
    summary = fields.EmbeddedDocumentField(
        DiagnosticSummary, default=DiagnosticSummary())
