# app/models/request_project_approval_model.py


from datetime import datetime

from flask import current_app
from mongoengine import (
    Document,
    EmbeddedDocument,
    fields,
    signals,
    ValidationError)

from app.models.project_model import Project
from app.schemas.project_schema import StepControlSchema
from app.models.shared_embedded_documents import ProjectReference


class RequestProjectApproval(Document):
    code = fields.SequenceField(required=True, value_decorator=str)
    project = fields.EmbeddedDocumentField(ProjectReference)
    status = fields.StringField(required=True, max_length=1, default="1")
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    isDeleted = fields.BooleanField(default=False)
    meta = {'collection': 'requests_project_approval',
            'ordering': ['-createdAt']}

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        if 'created' in kwargs and not kwargs['created']:
            # after update
            # is approved?
            if document.status == "2":
                schema = StepControlSchema(partial=True)
                project = Project.objects(id=document.project.id).first()
                for step in project.stepsProgress.steps:
                    if step.devName == "amblemaConfirmation":
                        data = {
                            'id': str(step.id),
                            'status': "3"
                        }
                        data = schema.load(data)
                        project.updateStep(data)
                        break


signals.post_save.connect(RequestProjectApproval.post_save,
                          sender=RequestProjectApproval)
