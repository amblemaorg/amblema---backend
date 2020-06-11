# app/models/peca_schedule_model.py

from datetime import datetime

from mongoengine import EmbeddedDocument, fields


class ScheduleActivity(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    subject = fields.StringField()
    startTime = fields.DateTimeField()
    endTime = fields.DateTimeField()
    description = fields.StringField()
