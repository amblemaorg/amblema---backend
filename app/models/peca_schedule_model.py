# app/models/peca_schedule_model.py

from datetime import datetime

from mongoengine import EmbeddedDocument, fields


class ScheduleActivity(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    devName = fields.StringField()
    activityId = fields.StringField()
    subject = fields.StringField()
    startTime = fields.DateTimeField()
    endTime = fields.DateTimeField()
    description = fields.StringField()
