# -*- coding: utf-8 -*-
# app/models/vademecum/upload_model.py

from datetime import datetime

from mongoengine import Document, EmbeddedDocument, fields

from app.models.vademecum.constants import UPLOAD_STATUSES


class UploadPage(EmbeddedDocument):
    """Lo que el procesamiento leyó en una página del compendio."""
    index = fields.IntField(required=True, min_value=0)
    headerText = fields.StringField(null=True)
    number = fields.IntField(null=True)
    isContinuation = fields.BooleanField(default=False)  # la "A" del encabezado
    title = fields.StringField(null=True)
    thumbnailPath = fields.StringField(null=True)


class UploadCut(EmbeddedDocument):
    """Páginas consecutivas que forman una ficha (o páginas excluidas)."""
    pages = fields.ListField(fields.IntField(min_value=0), default=list)
    number = fields.IntField(null=True)
    title = fields.StringField(null=True)
    excluded = fields.BooleanField(default=False)


class VademecumUpload(Document):
    originalFileName = fields.StringField(required=True)
    # Ruta relativa a VADEMECUM_STORAGE_PATH; el original se conserva para reprocesar.
    # Opcional: la ruta usa el id de la carga, que existe recién después del primer save
    originalPath = fields.StringField(null=True)
    originalSizeBytes = fields.LongField(required=True)
    pageCount = fields.IntField(null=True)  # lo completa el procesamiento
    sheetType = fields.ReferenceField("VademecumSheetType", required=True)
    seriesId = fields.ObjectIdField(null=True)
    status = fields.StringField(choices=UPLOAD_STATUSES, default="uploaded")
    progress = fields.IntField(min_value=0, max_value=100, default=0)
    errorMessage = fields.StringField(null=True)
    pages = fields.EmbeddedDocumentListField(UploadPage, default=list)
    proposedCuts = fields.EmbeddedDocumentListField(UploadCut, default=list)
    confirmedCuts = fields.EmbeddedDocumentListField(UploadCut, default=list)
    sheets = fields.ListField(fields.ReferenceField("VademecumSheet"), default=list)
    createdBy = fields.ReferenceField("User", required=True)
    processedAt = fields.DateTimeField(null=True)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {
        "collection": "vademecum_uploads",
        "indexes": [
            ("status", "-createdAt"),
            "sheetType",
        ],
    }

    def clean(self):
        self.updatedAt = datetime.utcnow()
