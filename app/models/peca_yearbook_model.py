# app/models/yearbook_model.py

from datetime import datetime
from email.policy import default
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields

from app.models.shared_embedded_documents import Approval


class PrintOption(EmbeddedDocument):
    print = fields.BooleanField(default=True)
    expandGallery = fields.BooleanField(default=True)
class Entity(EmbeddedDocument):
    name = fields.StringField()
    image = fields.StringField(null=True)
    content = fields.StringField()
    printOption = fields.EmbeddedDocumentField(PrintOption, default=PrintOption())

class Index(EmbeddedDocument):
    print = fields.BooleanField(default=True)
class Lapse(EmbeddedDocument):
    readingDiagnosticAnalysis = fields.StringField(default='')
    mathDiagnosticAnalysis = fields.StringField(default='')
    logicDiagnosticAnalysis = fields.StringField(default='')
    printOption = fields.EmbeddedDocumentField(PrintOption, default=PrintOption())

class Activity(EmbeddedDocument):
    name = fields.StringField(default='')
    print = fields.BooleanField(default=False)
    expandGallery = fields.BooleanField(default=False)
    lapse = fields.StringField(default='')
class Yearbook(EmbeddedDocument):
    historicalReview = fields.EmbeddedDocumentField(Entity, default=Entity())
    sponsor = fields.EmbeddedDocumentField(Entity, default=Entity())
    school = fields.EmbeddedDocumentField(Entity, default=Entity())
    coordinator = fields.EmbeddedDocumentField(Entity, default=Entity())
    lapse1 = fields.EmbeddedDocumentField(Lapse, default=Lapse())
    lapse2 = fields.EmbeddedDocumentField(Lapse, default=Lapse())
    lapse3 = fields.EmbeddedDocumentField(Lapse, default=Lapse())
    index = fields.EmbeddedDocumentField(Index, default=Index())
    activitiesPrint = fields.ListField(fields.EmbeddedDocumentField(Activity, default=Activity()))
    isInApproval = fields.BooleanField(default=False)
    approvalHistory = fields.EmbeddedDocumentListField(Approval)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
