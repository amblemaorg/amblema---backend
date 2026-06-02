from datetime import datetime
from mongoengine import Document, fields
from app.models.shared_embedded_documents import Approval

class YearbookApproval(Document):
    pecaId = fields.StringField(required=True)
    approval = fields.EmbeddedDocumentField(Approval)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {
        'collection': 'yearbook_approval',
        'indexes': [
            # Compound index for fast retrieval of approvals by pecaId, sorted by newest
            ('pecaId', '-createdAt'),
            # Index for fast retrieval of approved yearbooks
            'approval.status'
        ]
    }
