# -*- coding: utf-8 -*-
# app/models/vademecum/authorization_model.py

from datetime import datetime

from mongoengine import Document, fields


class VademecumAuthorization(Document):
    """Acceso de un docente externo por año escolar; vence al cambiar el año vigente."""
    account = fields.ReferenceField("VademecumTeacherAccount", required=True)
    # SchoolYear y no PecaProject: la autorización no lleva escuela
    schoolYear = fields.ReferenceField("SchoolYear", required=True)
    accessRequest = fields.ReferenceField("VademecumAccessRequest", null=True)
    approvedBy = fields.ReferenceField("User", required=True)
    approvedAt = fields.DateTimeField(default=datetime.utcnow)
    revokedAt = fields.DateTimeField(null=True)  # no se borra
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {
        "collection": "vademecum_authorizations",
        "indexes": [
            {"fields": ["account", "schoolYear"], "unique": True},
        ],
    }

    def clean(self):
        self.updatedAt = datetime.utcnow()
