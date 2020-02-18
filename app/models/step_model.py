# /app/models/step_model.py


from datetime import datetime
import json
from flask import current_app

from mongoengine import (
    Document,
    EmbeddedDocument,
    fields,
    signals,
    ValidationError)


from app.models.school_year_model import SchoolYear
from app.models.shared_embedded_documents import Link


class File(EmbeddedDocument):
    name = fields.StringField(required=True)
    url = fields.URLField(required=True)


class Step(Document):
    name = fields.StringField(required=True)
    type = fields.StringField(required=True, max_length=1)
    tag = fields.StringField(required=True, max_length=1)
    text = fields.StringField(required=True)
    date = fields.DateTimeField(required=False)
    file = fields.EmbeddedDocumentField(Link, is_file=True, null=True)
    video = fields.EmbeddedDocumentField(Link, null=True)
    schoolYear = fields.ReferenceField('SchoolYear', required=True)
    isStandard = fields.BooleanField(default=False)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'steps'}

    def clean(self):
        self.updatedAt = datetime.utcnow()

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        current_app.logger.info('StepModel pre_save')
        if not document.id:
            year = SchoolYear.objects(status="1", isDeleted=False).first()
            if not year:
                raise ValidationError(
                    message="There is not an active school year")
            document.schoolYear = year
        else:
            current_app.logger.info('before updated')


signals.pre_save.connect(Step.pre_save, sender=Step)
