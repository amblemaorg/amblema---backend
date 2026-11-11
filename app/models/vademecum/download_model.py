# -*- coding: utf-8 -*-
# app/models/vademecum/download_model.py

from datetime import datetime

from mongoengine import Document, EmbeddedDocument, fields

from app.models.vademecum.constants import ORIGINS


# Fotos del momento de la descarga: no cambian si después cambia la ficha o la matrícula

class DownloadSheet(EmbeddedDocument):
    id = fields.StringField(required=True)
    code = fields.StringField()
    title = fields.StringField()
    sheetTypeId = fields.StringField()
    sheetTypeName = fields.StringField()
    seriesId = fields.StringField(null=True)


class DownloadAccount(EmbeddedDocument):
    id = fields.StringField(required=True)
    email = fields.StringField()
    firstName = fields.StringField()
    lastName = fields.StringField()


class DownloadSchool(EmbeddedDocument):
    id = fields.StringField(required=True)
    name = fields.StringField()
    code = fields.StringField()
    stateId = fields.StringField(null=True)
    stateName = fields.StringField(null=True)


class DownloadSchoolYear(EmbeddedDocument):
    id = fields.StringField(required=True)
    name = fields.StringField()


class VademecumDownload(Document):
    """Registro histórico e inmutable: nunca se borra ni se edita."""
    sheet = fields.EmbeddedDocumentField(DownloadSheet, required=True)
    account = fields.EmbeddedDocumentField(DownloadAccount, required=True)
    teacherId = fields.StringField(null=True)  # Teacher.id en la escuela; null si externo
    school = fields.EmbeddedDocumentField(DownloadSchool, null=True)  # null si externo
    schoolYear = fields.EmbeddedDocumentField(DownloadSchoolYear, required=True)
    origin = fields.StringField(choices=ORIGINS, required=True)
    isRedownload = fields.BooleanField(required=True)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {
        "collection": "vademecum_downloads",
        "indexes": [
            ("account.id", "schoolYear.id", "-createdAt"),
            ("schoolYear.id", "createdAt"),
            ("sheet.id", "isRedownload"),
            ("account.id", "sheet.id"),
            # Solo una descarga que cuenta por (cuenta, ficha, año): evita contar dos veces
            # si llegan dos descargas simultáneas
            {"fields": ["account.id", "sheet.id", "schoolYear.id"], "unique": True,
             "partialFilterExpression": {"isRedownload": False},
             "name": "vademecum_downloads_first_per_year"},
            ("school.id", "schoolYear.id"),
            ("school.stateId", "schoolYear.id"),
            ("origin", "schoolYear.id"),
        ],
    }
