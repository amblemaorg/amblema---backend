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

from app.models.shared_embedded_documents import Link, CheckTemplate
from app.services.step_service import StepsService


class Step(Document):
    name = fields.StringField(required=True, unique_c=True)
    devName = fields.StringField(required=True, unique_c=True)
    tag = fields.StringField(required=True, max_length=1)
    hasText = fields.BooleanField(required=True, default=False)
    hasDate = fields.BooleanField(required=True, default=False)
    hasFile = fields.BooleanField(required=True, default=False)
    hasVideo = fields.BooleanField(required=True, default=False)
    hasChecklist = fields.BooleanField(required=True, default=False)
    hasUpload = fields.BooleanField(required=True, default=False)
    text = fields.StringField()
    file = fields.EmbeddedDocumentField(
        Link, is_file=True, null=True, default=None)
    video = fields.EmbeddedDocumentField(Link, null=True, default=None)
    checklist = fields.EmbeddedDocumentListField(
        CheckTemplate, null=True, default=None)
    approvalType = fields.StringField(required=True, max_length=1)
    schoolYear = fields.ReferenceField('SchoolYear', required=True)
    status = fields.StringField(default='1', max_length=1)
    isStandard = fields.BooleanField(default=False)
    sort = fields.IntField()
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'steps', 'ordering': ['+tag', '+sort']}

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
