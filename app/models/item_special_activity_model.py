# app/models/item_special_activity_model.py


from datetime import datetime
from bson import ObjectId

from flask import current_app
from mongoengine import fields, EmbeddedDocument

class ItemSpecialActivity(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    name = fields.StringField(required=True)
    description = fields.StringField(required=True)
    quantity = fields.IntField(default=0.0)
    unitPrice = fields.FloatField(default=0.0)
    tax = fields.FloatField(default=0.0)
    subtotal = fields.FloatField(default=0.0)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)