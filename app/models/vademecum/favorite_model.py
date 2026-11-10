# -*- coding: utf-8 -*-
# app/models/vademecum/favorite_model.py

from datetime import datetime

from mongoengine import Document, fields


class VademecumFavorite(Document):
    """Quitar un favorito borra el documento (sin borrado lógico)."""
    account = fields.ReferenceField("VademecumTeacherAccount", required=True)
    sheet = fields.ReferenceField("VademecumSheet", required=True)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {
        "collection": "vademecum_favorites",
        "indexes": [
            {"fields": ["account", "sheet"], "unique": True},
        ],
    }

    def clean(self):
        self.updatedAt = datetime.utcnow()
