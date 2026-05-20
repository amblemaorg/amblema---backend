# app/models/olympics_history_model.py

from datetime import datetime
from mongoengine import Document, EmbeddedDocument, fields

class OlympicsHistoryData(EmbeddedDocument):
    regionalClassified = fields.IntField(default=0)
    regionalGold = fields.IntField(default=0)
    regionalSilver = fields.IntField(default=0)
    regionalBronze = fields.IntField(default=0)
    nationalClassified = fields.IntField(default=0)
    nationalGold = fields.IntField(default=0)
    nationalSilver = fields.IntField(default=0)
    nationalBronze = fields.IntField(default=0)

class OlympicsHistory(Document):
    mathOlympics = fields.EmbeddedDocumentField(OlympicsHistoryData, default=OlympicsHistoryData())
    readingOlympics = fields.EmbeddedDocumentField(OlympicsHistoryData, default=OlympicsHistoryData())
    isDeleted = fields.BooleanField(default=False)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    
    meta = {'collection': 'olympics_history', 'strict': False}
