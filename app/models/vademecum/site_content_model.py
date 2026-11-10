# -*- coding: utf-8 -*-
# app/models/vademecum/site_content_model.py

from datetime import datetime

from mongoengine import Document, fields


class VademecumSiteContent(Document):
    """Texto editable de una sección del sitio (home, about, access_request, ...)."""
    key = fields.StringField(required=True)
    title = fields.StringField(null=True)
    body = fields.StringField(null=True)
    updatedBy = fields.ReferenceField("User", null=True)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {
        "collection": "vademecum_site_content",
        "indexes": [
            {"fields": ["key"], "unique": True},
        ],
    }

    def clean(self):
        self.updatedAt = datetime.utcnow()
