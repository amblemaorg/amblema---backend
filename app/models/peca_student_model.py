# app/models/peca_student_model.py


from datetime import datetime
from bson import ObjectId

from flask import current_app
from mongoengine import fields, Document, EmbeddedDocument, signals


class Diagnostic(EmbeddedDocument):
    multiplicationsPerMin = fields.IntField()
    multiplicationsPerMinIndex = fields.FloatField()
    operationsPerMin = fields.IntField()
    operationsPerMinIndex = fields.FloatField()
    wordsPerMin = fields.IntField()
    wordsPerMinIndex = fields.FloatField()
    mathDate = fields.DateTimeField()
    logicDate = fields.DateTimeField()
    readingDate = fields.DateTimeField()

    def calculateIndex(self, setting):
        if self.multiplicationsPerMin:
            self.multiplicationsPerMinIndex = self.multiplicationsPerMin / \
                setting.multiplicationsPerMin
        if self.operationsPerMin:
            self.operationsPerMinIndex = self.operationsPerMin / setting.operationsPerMin
        if self.wordsPerMin:
            self.wordsPerMinIndex = self.wordsPerMin / setting.wordsPerMin


class Student(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    firstName = fields.StringField()
    lastName = fields.StringField()
    cardId = fields.StringField()
    cardType = fields.StringField()
    birthdate = fields.DateTimeField()
    gender = fields.StringField(max_length=1)
    lapse1 = fields.EmbeddedDocumentField(Diagnostic)
    lapse2 = fields.EmbeddedDocumentField(Diagnostic)
    lapse3 = fields.EmbeddedDocumentField(Diagnostic)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
