# app/models/yearbook_model.py

from datetime import datetime
from email.policy import default
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields

from app.models.shared_embedded_documents import Approval

class Entity(EmbeddedDocument):
    name = fields.StringField()
    image = fields.StringField(null=True)
    content = fields.StringField()
class Lapse(EmbeddedDocument):
    readingDiagnosticAnalysis = fields.StringField(default='')
    mathDiagnosticAnalysis = fields.StringField(default='')
    logicDiagnosticAnalysis = fields.StringField(default='')
class GroupPhoto(EmbeddedDocument):
    name = fields.StringField(null=True)
    image = fields.StringField(null=True)
    content = fields.StringField(null=True)
    groupedSections = fields.ListField(fields.StringField())

class Yearbook(EmbeddedDocument):
    meta = {'strict': False}
    historicalReview = fields.EmbeddedDocumentField(Entity, default=Entity())
    sponsor = fields.EmbeddedDocumentField(Entity, default=Entity())
    school = fields.EmbeddedDocumentField(Entity, default=Entity())
    coordinator = fields.EmbeddedDocumentField(Entity, default=Entity())
    groupPhoto = fields.EmbeddedDocumentField(GroupPhoto, default=GroupPhoto())
    lapse1 = fields.EmbeddedDocumentField(Lapse, default=Lapse())
    lapse2 = fields.EmbeddedDocumentField(Lapse, default=Lapse())
    lapse3 = fields.EmbeddedDocumentField(Lapse, default=Lapse())
    isInApproval = fields.BooleanField(default=False)

    updatedAt = fields.DateTimeField(default=datetime.utcnow)
