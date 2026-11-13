# -*- coding: utf-8 -*-
# app/models/vademecum/area_model.py

from datetime import datetime

from mongoengine import Document, fields

from app.models.vademecum.constants import ACTIVE_STATUSES, NOT_DELETED


class VademecumArea(Document):
    """Área o eje temático (la lista la define AmbLeMa)."""
    name = fields.StringField(required=True)
    sort = fields.IntField(required=True)
    status = fields.StringField(choices=ACTIVE_STATUSES, default="1")
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {
        "collection": "vademecum_areas",
        "indexes": [
            {"fields": ["name"], "unique": True, "partialFilterExpression": NOT_DELETED},
            ("isDeleted", "status", "sort"),
        ],
    }

    def clean(self):
        self.updatedAt = datetime.utcnow()
