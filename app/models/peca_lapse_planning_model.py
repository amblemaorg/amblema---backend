# app/models/peca_lapse_planning_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields

from app.models.shared_embedded_documents import Link
from app.models.peca_activity_yearbook_model import ActivityYearbook


class LapsePlanningPeca(EmbeddedDocument):
    name = fields.StringField(default="Planificación de lapso")
    proposalFundationFile = fields.EmbeddedDocumentField(Link)
    proposalFundationDescription = fields.StringField()
    meetingDescription = fields.StringField()
    isStandard = fields.BooleanField(default=True)
    attachedFile = fields.EmbeddedDocumentField(
        Link, is_file=True)
    meetingDate = fields.DateTimeField()
    yearbook = fields.EmbeddedDocumentField(ActivityYearbook)
    status = fields.StringField(default="1", max_length=1)
