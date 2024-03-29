# app/models/peca_activities_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields, signals

from app.models.shared_embedded_documents import Link, Approval, CheckElement
from app.models.peca_activity_yearbook_model import ActivityYearbook



class ActivityFields(EmbeddedDocument):
    id = fields.StringField(required=True)
    name = fields.StringField(required=True)
    devName = fields.StringField(required=True)
    hasText = fields.BooleanField(required=True, default=False)
    hasDate = fields.BooleanField(required=True, default=False)
    hasFile = fields.BooleanField(required=True, default=False)
    hasVideo = fields.BooleanField(required=True, default=False)
    hasChecklist = fields.BooleanField(required=True, default=False)
    hasUpload = fields.BooleanField(required=True, default=False)
    text = fields.StringField()
    file = fields.EmbeddedDocumentField(Link)
    video = fields.EmbeddedDocumentField(Link)
    checklist = fields.EmbeddedDocumentListField(CheckElement)
    date = fields.DateTimeField(null=True)
    uploadedFile = fields.EmbeddedDocumentField(
        Link, is_file=True, size=1024, null=True, default=None)
    approvalType = fields.StringField(required=True, max_length=1)
    isStandard = fields.BooleanField(default=False)
    percent = fields.FloatField(default=0)
    status = fields.StringField(default="1", max_length=1)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    order = fields.IntField(default=100)
    meta = {'allow_inheritance': True}
    
class ActivityPeca(ActivityFields):
    approvalHistory = fields.EmbeddedDocumentListField(Approval)
    yearbook = fields.EmbeddedDocumentField(
        ActivityYearbook, default=ActivityYearbook())

    def approve(self):
        self.status = "3"

    def checkStatus(self):
        fields = {
            'hasDate': 'date',
            'hasUpload': 'uploadedFile',
            'hasChecklist': 'checklist'
        }
        if self.approvalType == "2" or self.approvalType == '3':
            approved = True
            for key in fields.keys():
                if self[key]:
                    if key == 'hasChecklist':
                        for reg in self.checklist:
                            if not reg.checked:
                                approved = False
                    if not self[fields[key]]:
                        approved = False
            if approved:
                self.approve()
        if self.approvalType == "5":
            self.approve()

    def clean(self):
        self.updatedAt = datetime.utcnow()
