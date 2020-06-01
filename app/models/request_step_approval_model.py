# app/models/request_step_approval_model.py


from datetime import datetime

from flask import current_app
from mongoengine import (
    Document,
    EmbeddedDocument,
    fields,
    signals,
    ValidationError)

from app.models.project_model import Project, Approval, CheckElement
from app.models.shared_embedded_documents import Link
from app.models.user_model import User


class RequestStepApproval(Document):
    stepId = fields.StringField(required=True)
    project = fields.ReferenceField(Project, required=True)
    user = fields.ReferenceField(User)
    comments = fields.StringField()
    status = fields.StringField(required=True, max_length=1, default="1")
    stepName = fields.StringField()
    stepDevName = fields.StringField()
    stepTag = fields.StringField()
    stepHasText = fields.BooleanField()
    stepHasDate = fields.BooleanField()
    stepHasFile = fields.BooleanField()
    stepHasVideo = fields.BooleanField()
    stepHasChecklist = fields.BooleanField()
    stepHasUpload = fields.BooleanField()
    stepText = fields.StringField()
    stepFile = fields.EmbeddedDocumentField(Link)
    stepVideo = fields.EmbeddedDocumentField(Link)
    stepChecklist = fields.EmbeddedDocumentListField(CheckElement)
    stepDate = fields.DateTimeField(null=True)
    stepUploadedFile = fields.EmbeddedDocumentField(
        Link, is_file=True, null=True, default=None)
    stepIsStandard = fields.BooleanField()
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    isDeleted = fields.BooleanField(default=False)
    meta = {'collection': 'requests_step_approval'}
