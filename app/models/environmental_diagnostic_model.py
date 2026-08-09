# app/models/environmental_diagnostic_model.py

from datetime import datetime
from mongoengine import Document, fields


class EnvironmentalDiagnosticEvaluator(Document):
    pecaId = fields.StringField(required=True)
    lapse = fields.StringField(required=True)
    name = fields.StringField(required=True)
    email = fields.EmailField(required=True)
    phone = fields.StringField(required=True)
    token = fields.StringField(required=True, unique=True)
    hasEvaluated = fields.BooleanField(default=False)
    evaluatedAt = fields.DateTimeField(null=True)
    results = fields.DictField(default={})
    index = fields.FloatField(null=True)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'environmental_diagnostic_evaluators',
        'indexes': ['pecaId', 'lapse', 'token', 'isDeleted']
    }

    def clean(self):
        self.updatedAt = datetime.utcnow()
