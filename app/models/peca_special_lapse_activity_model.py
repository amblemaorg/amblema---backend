# app/models/special_activity_model.py


from datetime import datetime
from bson import ObjectId

from flask import current_app
from mongoengine import fields, EmbeddedDocument
from app.models.shared_embedded_documents import Approval

from app.models.peca_activity_yearbook_model import ActivityYearbook


class ItemSpecialActivity(EmbeddedDocument):
    name = fields.StringField(required=True)
    description = fields.StringField(required=True)
    quantity = fields.IntField(default=0.0)
    unitPrice = fields.FloatField(default=0.0)
    tax = fields.FloatField(default=0.0)
    subtotal = fields.FloatField(default=0.0)


class SpecialActivityPeca(EmbeddedDocument):
    name = fields.StringField(default="Actividad especial de lapso")
    activityDate = fields.DateTimeField()
    # approvalStatus = ("1": "pending", "2": "approved", "3": "rejected", "4": "cancelled")
    itemsActivities = fields.EmbeddedDocumentListField(ItemSpecialActivity)
    total = fields.FloatField(default=0.0)
    isDeleted = fields.BooleanField(default=False)
    approvalHistory = fields.EmbeddedDocumentListField(Approval)
    isInApproval = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    yearbook = fields.EmbeddedDocumentField(
        ActivityYearbook, default=ActivityYearbook())
