# app/models/peca_initial_workshop_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields

from app.models.shared_embedded_documents import Link, Approval


class Image(EmbeddedDocument):
    image = fields.URLField()
    description = fields.StringField()
    status = fields.StringField()


class InitialWorkshopPeca(EmbeddedDocument):
    name = fields.StringField(default="Taller inicial")
    agreementFile = fields.EmbeddedDocumentField(
        Link)
    agreementDescription = fields.StringField()
    planningMeetingFile = fields.EmbeddedDocumentField(
        Link)
    planningMeetingDescription = fields.StringField()
    teachersMeetingFile = fields.EmbeddedDocumentField(
        Link)
    teachersMeetingDescription = fields.StringField()
    isStandard = fields.BooleanField(default=True)
    description = fields.StringField()
    images = fields.EmbeddedDocumentListField(Image)
    isInApproval = fields.BooleanField(default=False)
    approvalHistory = fields.EmbeddedDocumentListField(Approval)
