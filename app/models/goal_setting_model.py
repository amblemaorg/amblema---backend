# app/models/goal_setting_model.py

from datetime import datetime

from mongoengine import EmbeddedDocument, fields


class GradeSetting(EmbeddedDocument):
    multitplicationsPerMin = fields.IntField()
    operationsPerMin = fields.IntField()
    wordsPerMin = fields.IntField()


class GoalSetting(EmbeddedDocument):
    grade1 = fields.EmbeddedDocumentField(GradeSetting)
    grade2 = fields.EmbeddedDocumentField(GradeSetting)
    grade3 = fields.EmbeddedDocumentField(GradeSetting)
    grade4 = fields.EmbeddedDocumentField(GradeSetting)
    grade5 = fields.EmbeddedDocumentField(GradeSetting)
    grade6 = fields.EmbeddedDocumentField(GradeSetting)
