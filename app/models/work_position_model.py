# app/models/work_position_model.py


from datetime import datetime
from bson import ObjectId
import re

from mongoengine import (
    Document,
    EmbeddedDocument,
    fields,
    signals)


class WorkPosition(Document):
    name = fields.StringField(required=True)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)