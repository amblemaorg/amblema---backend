from datetime import datetime
from mongoengine import Document, fields
from app.models.shared_embedded_documents import Approval

class YearbookApproval(Document):
    pecaId = fields.StringField(required=True)
    approval = fields.EmbeddedDocumentField(Approval)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'yearbook_approval'}
