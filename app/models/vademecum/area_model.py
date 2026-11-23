# -*- coding: utf-8 -*-
# app/models/vademecum/area_model.py

from datetime import datetime

from mongoengine import Document, fields

from app.models.vademecum.constants import ACTIVE_STATUSES, NOT_DELETED


class VademecumArea(Document):
    """Área o eje temático (la lista la define AmbLeMa).

    `sheetTypes`: tipos de ficha a los que aplica (una o varios; 2026-11-23). Una ficha solo
    puede tener áreas de su tipo (código 121).
    """
    name = fields.StringField(required=True)
    sheetTypes = fields.ListField(fields.ReferenceField("VademecumSheetType"), default=list)
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

    def applies_to(self, sheetType):
        """True si el área sirve para ese tipo de ficha (documento o id)."""
        typeId = getattr(sheetType, "id", sheetType)
        return any(getattr(ref, "id", ref) == typeId for ref in self.sheetTypes)
