# /app/models/step_model.py


from datetime import datetime
import json
from flask import current_app

from mongoengine import (
    Document,
    EmbeddedDocument,
    fields)


from app.models.school_year_model import SchoolYear


class File(EmbeddedDocument):
    name = fields.StringField(required=True)
    url = fields.URLField(required=True)


class Step(Document):
    name = fields.StringField(required=True)
    type = fields.StringField(required=True, max_length=1)
    tag = fields.StringField(required=True, max_length=1)
    text = fields.StringField(required=True)
    date = fields.DateTimeField(required=False)
    file = fields.EmbeddedDocumentField(File, is_file=True)
    schoolYear = fields.ReferenceField('SchoolYear', required=True)
    isStandard = fields.BooleanField(default=False)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'steps'}

    def clean(self):
        self.updatedAt = datetime.utcnow()
