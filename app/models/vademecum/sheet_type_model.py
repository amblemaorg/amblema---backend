# -*- coding: utf-8 -*-
# app/models/vademecum/sheet_type_model.py

from datetime import datetime

from bson import ObjectId
from mongoengine import Document, EmbeddedDocument, ValidationError, fields

from app.models.vademecum.constants import (
    GRADES, ACTIVE_STATUSES, HEX_COLOR_REGEX, NOT_DELETED)


class SheetSeries(EmbeddedDocument):
    """Serie por rango de grados dentro de un tipo (p. ej. Ingenio Matemático 3.º y 4.º)."""
    id = fields.ObjectIdField(default=ObjectId)
    name = fields.StringField(required=True)
    code = fields.StringField(required=True, max_length=4)
    grades = fields.ListField(fields.StringField(choices=GRADES), default=list)
    sort = fields.IntField(default=0)
    isDeleted = fields.BooleanField(default=False)


class VademecumSheetType(Document):
    name = fields.StringField(required=True)
    # Texto con que empieza el encabezado de cada página del PDF (detección de cortes)
    headerName = fields.StringField(required=True)
    codePrefix = fields.StringField(required=True, max_length=4)
    color = fields.StringField(required=True, regex=HEX_COLOR_REGEX)
    sectionTitle = fields.StringField(null=True)
    sectionText = fields.StringField(null=True)
    sort = fields.IntField(required=True)
    series = fields.EmbeddedDocumentListField(SheetSeries, default=list)
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
        codes = [s.code for s in self.series if not s.isDeleted]
        if len(codes) != len(set(codes)):
            raise ValidationError("Series codes must be unique within the sheet type",
                                  errors={"series": "Duplicated series code"})

    def active_series(self):
        return [s for s in self.series if not s.isDeleted]

    def get_series(self, seriesId):
        """Returns the series with that id (ObjectId or str), or None."""
        if not seriesId:
            return None
        for series in self.series:
            if str(series.id) == str(seriesId):
                return series
        return None
