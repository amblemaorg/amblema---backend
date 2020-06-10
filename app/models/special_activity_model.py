# app/models/special_activity_model.py


from datetime import datetime
from bson import ObjectId

from flask import current_app
from mongoengine import fields, EmbeddedDocument
from app.models.item_special_activity_model import ItemSpecialActivity

class SpecialActivity(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    name = fields.StringField(default="Actividad especial")
    activityDate = fields.DateTimeField(required=True)
    # approvalStatus = ("1": "pending", "2": "approved", "3": "rejected", "4": "cancelled")
    approvalStatus = fields.StringField(default='1', max_length=1)
    itemsActivities = fields.EmbeddedDocumentListField(ItemSpecialActivity)
    total = fields.FloatField(default=0.0)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)