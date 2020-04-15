# app/models/request_content_approval_model.py


from datetime import datetime
from app.models.peca_project_model import PecaProject

from flask import current_app
from mongoengine import (
    Document,
    EmbeddedDocument,
    fields,
    signals,
    ValidationError)


class RequestContentApproval(Document):
    code = fields.SequenceField(required=True, value_decorator=str)
    pecaId = fields.ObjectIdField(required=True)
    recordId = fields.ObjectIdField(required=True)
    type = fields.StringField()
    comments = fields.StringField()
    status = fields.StringField(required=True, max_length=1, default="1")
    content = fields.GenericEmbeddedDocumentField()
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    isDeleted = fields.BooleanField(default=False)
    meta = {'collection': 'requests_content_approval'}

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if document.id is not None:
            oldDocument = document.__class__.objects(id=document.id).first()
            if document.status != oldDocument.status:
                if document.type == "schoolSlider":
                    peca = PecaProject.objects(id=document.pecaId).first()
                    for slider in peca.school.slider:
                        if slider.id == document.recordId:
                            slider.approvalStatus = document.status
                            break
                    peca.save()


signals.pre_save.connect(RequestContentApproval.pre_save,
                         sender=RequestContentApproval)
