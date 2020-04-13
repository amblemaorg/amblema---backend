# app/models/request_content_approval_model.py


from datetime import datetime

from flask import current_app
from mongoengine import (
    Document,
    EmbeddedDocument,
    fields,
    signals,
    ValidationError)


class RequestContentApproval(Document):
    code = fields.SequenceField(required=True, value_decorator=str)
    parentId = fields.ObjectIdField(required=True)
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
        current_app.logger.info("presave")

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        if 'created' in kwargs and kwargs['created']:
            current_app.logger.info("postsave")


signals.pre_save.connect(RequestContentApproval.pre_save,
                         sender=RequestContentApproval)
signals.post_save.connect(RequestContentApproval.post_save,
                          sender=RequestContentApproval)
