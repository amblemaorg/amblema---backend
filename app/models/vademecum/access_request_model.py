# -*- coding: utf-8 -*-
# app/models/vademecum/access_request_model.py

from datetime import datetime

from mongoengine import Document, fields

from app.models.vademecum.constants import REQUEST_STATUSES


class VademecumAccessRequest(Document):
    """Solicitud de quien no está en la matrícula; se envía sin cuenta."""
    account = fields.ReferenceField("VademecumTeacherAccount", null=True)  # se llena al aprobar
    email = fields.EmailField(required=True)
    firstName = fields.StringField(required=True)
    lastName = fields.StringField(required=True)
    cardId = fields.StringField(null=True)
    phone = fields.StringField(null=True)
    institution = fields.StringField(required=True)  # texto libre, solo de referencia
    schoolYear = fields.ReferenceField("SchoolYear", required=True)
    status = fields.StringField(choices=REQUEST_STATUSES, default="pending")
    rejectionReason = fields.StringField(null=True)
    reviewedBy = fields.ReferenceField("User", null=True)
    reviewedAt = fields.DateTimeField(null=True)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {
        "collection": "vademecum_access_requests",
        "indexes": [
            # Una sola solicitud pendiente por email y año
            {"fields": ["email", "schoolYear"], "unique": True,
             "partialFilterExpression": {"status": "pending"}},
            ("status", "-createdAt"),
        ],
    }

    def clean(self):
        self.updatedAt = datetime.utcnow()
        if self.email:
            self.email = self.email.lower().strip()
