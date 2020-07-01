# app/models/peca_activities_slider_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields

from app.models.shared_embedded_documents import Approval


class ActivitiesSlider(EmbeddedDocument):
    slider = fields.ListField(fields.StringField())
    isInApproval = fields.BooleanField(default=False)
    approvalHistory = fields.EmbeddedDocumentListField(Approval)
