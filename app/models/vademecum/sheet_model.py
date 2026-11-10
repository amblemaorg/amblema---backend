# -*- coding: utf-8 -*-
# app/models/vademecum/sheet_model.py

from datetime import datetime

from mongoengine import Document, EmbeddedDocument, ValidationError, fields

from app.models.vademecum.constants import GRADES, SHEET_STATUSES, NOT_DELETED

PUBLISH_ERROR_STATUS = "113"


def build_sheet_code(codePrefix, seriesCode, number):
    """HT-41 without series, IM34-1 with series."""
    return u"{}{}-{}".format(codePrefix, seriesCode or u"", number)


class SheetFile(EmbeddedDocument):
    """PDF optimizado y sus imágenes; rutas relativas a VADEMECUM_STORAGE_PATH."""
    pdfPath = fields.StringField(required=True)
    sizeBytes = fields.LongField()
    pageCount = fields.IntField()
    thumbnailPath = fields.StringField(null=True)
    previewPath = fields.StringField(null=True)
    generatedAt = fields.DateTimeField(default=datetime.utcnow)


class VademecumSheet(Document):
    code = fields.StringField()
    sheetType = fields.ReferenceField("VademecumSheetType", required=True)
    seriesId = fields.ObjectIdField(null=True)
    number = fields.IntField(required=True, min_value=1)
    title = fields.StringField(required=True)
    description = fields.StringField(null=True)
    areas = fields.ListField(fields.ReferenceField("VademecumArea"), default=list)
    grades = fields.ListField(fields.StringField(choices=GRADES), default=list)
    upload = fields.ReferenceField("VademecumUpload", null=True)
    sourcePages = fields.ListField(fields.IntField(min_value=0), default=list)
    file = fields.EmbeddedDocumentField(SheetFile, null=True)
    searchText = fields.StringField(null=True)
    status = fields.StringField(choices=SHEET_STATUSES, default="draft")
    publishedAt = fields.DateTimeField(null=True)
    fileReplacedAt = fields.DateTimeField(null=True)
    # Contadores desnormalizados; se actualizan solo con $inc
    downloadCount = fields.IntField(default=0)
    ratingCount = fields.IntField(default=0)
    ratingSum = fields.IntField(default=0)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {
        "collection": "vademecum_sheets",
        "indexes": [
            # seriesId ausente cuenta como null: Hora TAL 41 tampoco se repite
            {"fields": ["sheetType", "seriesId", "number"], "unique": True,
             "partialFilterExpression": NOT_DELETED},
            {"fields": ["code"], "unique": True, "partialFilterExpression": NOT_DELETED},
            {"fields": ["$title", "$description", "$searchText"],
             "default_language": "spanish",
             "weights": {"title": 10, "description": 5, "searchText": 1}},
            ("status", "-publishedAt"),
            ("status", "-downloadCount"),
            ("status", "sheetType", "grades"),
        ],
    }

    def clean(self):
        self.updatedAt = datetime.utcnow()
        if self.sheetType and self.number:
            series = self.sheetType.get_series(self.seriesId)
            if self.seriesId and series is None:
                raise ValidationError("Series does not belong to the sheet type",
                                      errors={"seriesId": "Series not found in sheet type"})
            if not self.seriesId and self.sheetType.active_series():
                raise ValidationError("Sheet type requires a series",
                                      errors={"seriesId": "Series is required"})
            self.code = build_sheet_code(
                self.sheetType.codePrefix, series.code if series else None, self.number)

    def publish_errors(self):
        """Missing data to publish, in the API error format; {} when it can be published."""
        errors = {}
        if not (self.description or u"").strip():
            errors["description"] = [{"status": PUBLISH_ERROR_STATUS,
                                      "msg": "Description is required to publish"}]
        if not self.grades:
            errors["grades"] = [{"status": PUBLISH_ERROR_STATUS,
                                 "msg": "At least one grade is required to publish"}]
        if not self.file:
            errors["file"] = [{"status": PUBLISH_ERROR_STATUS,
                               "msg": "A generated file is required to publish"}]
        return errors
