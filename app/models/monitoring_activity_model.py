# app/models/monitoring_activity_model.py


from datetime import datetime
from bson import ObjectId

from flask import current_app
from mongoengine import fields, EmbeddedDocument


class DetailActivity(EmbeddedDocument):
    description = fields.StringField()
    image = fields.URLField(null=True)


class MonitoringActivity(EmbeddedDocument):
    environmentActivities = fields.EmbeddedDocumentListField(DetailActivity, max_length=4)
    readingActivities = fields.EmbeddedDocumentListField(DetailActivity, max_length=4)
    mathActivities = fields.EmbeddedDocumentListField(DetailActivity, max_length=4)