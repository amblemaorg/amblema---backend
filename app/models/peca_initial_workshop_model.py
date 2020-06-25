# app/models/peca_initial_workshop_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields

from app.models.shared_embedded_documents import Link, Approval
from app.models.peca_activity_yearbook_model import ActivityYearbook


class Image(EmbeddedDocument):
    image = fields.StringField()
    description = fields.StringField()
    status = fields.StringField()


class InitialWorkshopPeca(EmbeddedDocument):
    name = fields.StringField(default="Taller inicial")
    # agreementFile = fields.EmbeddedDocumentField(
    #    Link)
    #agreementDescription = fields.StringField()
    # planningMeetingFile = fields.EmbeddedDocumentField(
    #    Link)
    #planningMeetingDescription = fields.StringField()
    # teachersMeetingFile = fields.EmbeddedDocumentField(
    #    Link)
    #teachersMeetingDescription = fields.StringField()
    isStandard = fields.BooleanField(default=True)
    description = fields.StringField()
    images = fields.EmbeddedDocumentListField(Image)
    workshopPlace = fields.StringField()
    workshopDate = fields.DateTimeField()
    isInApproval = fields.BooleanField(default=False)
    approvalHistory = fields.EmbeddedDocumentListField(Approval)
    yearbook = fields.EmbeddedDocumentField(
        ActivityYearbook, default=ActivityYearbook())
