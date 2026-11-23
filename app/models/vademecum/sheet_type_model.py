# -*- coding: utf-8 -*-
# app/models/vademecum/sheet_type_model.py

from datetime import datetime

from mongoengine import Document, fields

from app.models.vademecum.constants import ACTIVE_STATUSES, HEX_COLOR_REGEX, NOT_DELETED


class VademecumSheetType(Document):
    name = fields.StringField(required=True)
    # Texto con que empieza el encabezado de cada página del PDF (detección de cortes)
    headerName = fields.StringField(required=True)
    codePrefix = fields.StringField(required=True, max_length=4)
    color = fields.StringField(required=True, regex=HEX_COLOR_REGEX)
    sectionTitle = fields.StringField(null=True)
    sectionText = fields.StringField(null=True)
    sort = fields.IntField(required=True)
    status = fields.StringField(choices=ACTIVE_STATUSES, default="1")
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {
        "collection": "vademecum_sheet_types",
        "indexes": [
            {"fields": ["codePrefix"], "unique": True,
             "partialFilterExpression": NOT_DELETED},
            ("isDeleted", "status", "sort"),
        ],
    }

    def clean(self):
        self.updatedAt = datetime.utcnow()
