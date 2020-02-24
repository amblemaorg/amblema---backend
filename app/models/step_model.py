# /app/models/step_model.py


from datetime import datetime
import json
from bson import ObjectId

from flask import current_app
from mongoengine import (
    Document,
    EmbeddedDocument,
    fields,
    signals)

from app.models.shared_embedded_documents import Link
from app.services.step_service import StepsService


class Check(EmbeddedDocument):
    id = fields.ObjectIdField(default=ObjectId())
    name = fields.StringField(required=True)


class Step(Document):
    name = fields.StringField(required=True, unique_c=True)
    devName = fields.StringField(required=True, unique_c=True)
    type = fields.StringField(required=True, max_length=1)
    tag = fields.StringField(required=True, max_length=1)
    text = fields.StringField(required=True)
    date = fields.DateTimeField(required=False, null=True, default=None)
    file = fields.EmbeddedDocumentField(
        Link, is_file=True, null=True, default=None)
    video = fields.EmbeddedDocumentField(Link, null=True, default=None)
    checklist = fields.EmbeddedDocumentListField(Check)
    schoolYear = fields.ReferenceField('SchoolYear', required=True)
    status = fields.StringField(default='1', max_length=1)
    isStandard = fields.BooleanField(default=False)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'steps'}

    def clean(self):
        self.updatedAt = datetime.utcnow()

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        stepsService = StepsService()
        if not document.id:
            stepsService.handler_steps_before_create(document)
        else:
            oldDocument = document.__class__.objects.get(id=document.id)
            stepsService.handler_steps_before_upd(document, oldDocument)

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        stepsService = StepsService()
        if 'created' in kwargs and kwargs['created']:
            stepsService.handler_steps_after_create(document)


signals.pre_save.connect(Step.pre_save, sender=Step)
signals.post_save.connect(Step.post_save, sender=Step)
