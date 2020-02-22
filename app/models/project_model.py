# app/models/project_model.py


from datetime import datetime

from flask import current_app
from mongoengine import (
    Document,
    EmbeddedDocument,
    fields,
    signals,
    ValidationError)

from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.coordinator_user_model import CoordinatorUser
from app.models.shared_embedded_documents import Link
from app.services.project_service import ProjectService


class CheckElement(EmbeddedDocument):
    id = fields.ObjectIdField()
    name = fields.StringField()
    checked = fields.BooleanField(default=False)


class StepControl(EmbeddedDocument):
    id = fields.StringField(required=True)
    name = fields.StringField(required=True)
    type = fields.StringField(required=True, max_length=1)
    tag = fields.StringField(required=True, max_length=1)
    text = fields.StringField(required=True)
    date = fields.DateTimeField(null=True)
    file = fields.EmbeddedDocumentField(Link, null=True)
    video = fields.EmbeddedDocumentField(Link, null=True)
    checklist = fields.EmbeddedDocumentListField(CheckElement)
    uploadedFile = fields.EmbeddedDocumentField(
        Link, is_file=True, null=True, default=None)
    isStandard = fields.BooleanField(default=False)
    status = fields.StringField(default="1", max_length=1)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)

    def approve(self):
        self.status = "2"

    def clean(self):
        self.updatedAt = datetime.utcnow()


class StepsProgress(EmbeddedDocument):
    general = fields.IntField(default=0)
    school = fields.IntField(default=0)
    sponsor = fields.IntField(default=0)
    coordinator = fields.IntField(default=0)
    steps = fields.EmbeddedDocumentListField(StepControl)


class Project(Document):
    code = fields.SequenceField(required=True, value_decorator=str)
    school = fields.ReferenceField('SchoolUser')
    sponsor = fields.ReferenceField('SponsorUser')
    coordinator = fields.ReferenceField('CoordinatorUser')
    schoolYear = fields.LazyReferenceField('SchoolYear')
    stepsProgress = fields.EmbeddedDocumentField(StepsProgress)
    status = fields.StringField(default='1')
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    isDeleted = fields.BooleanField(default=False)
    meta = {'collection': 'projects'}

    def updateProgress(self):
        nGeneralSteps = 0
        nSchoolSteps = 0
        nCoordinatorSteps = 0
        nSponsorSteps = 0
        nApprovedGeneralSteps = 0
        nApprovedSchoolSteps = 0
        nApprovedCoordinatorSteps = 0
        nApprovedSponsorSteps = 0

        for step in self.stepsProgress.steps:
            if step.tag == "1":
                nGeneralSteps += 1
                nApprovedGeneralSteps += 1 if step.status == "2" else 0
            if step.tag == "2":
                nCoordinatorSteps += 1
                nApprovedCoordinatorSteps += 1 if step.status == "2" else 0
            if step.tag == "3":
                nSponsorSteps += 1
                nApprovedSponsorSteps += 1 if step.status == "2" else 0
            if step.tag == "4":
                nSchoolSteps += 1
                nApprovedSchoolSteps += 1 if step.status == "2" else 0
        self.stepsProgress.general = 100 if nGeneralSteps == 0 else nApprovedGeneralSteps/nGeneralSteps
        self.stepsProgress.school = 100 if nSchoolSteps == 0 else nApprovedSchoolSteps/nSchoolSteps
        self.stepsProgress.sponsor = 100 if nSponsorSteps == 0 else nApprovedSponsorSteps/nSponsorSteps
        self.stepsProgress.coordinator = 100 if nCoordinatorSteps == 0 else nApprovedCoordinatorSteps/nCoordinatorSteps

    def updateStep(self, step):
        for myStep in self.stepsProgress.steps:
            if step.id == myStep.id:
                isUpdated = False
                if myStep.type == "1":
                    myStep.status = step.status
                    isUpdated = True
                elif myStep.type == "2":
                    if step.date:
                        myStep.date = step.date
                        myStep.approve()
                        isUpdated = True
                elif myStep.type == "3":
                    if step.uploadedFile:
                        myStep.uploadedFile = step.uploadedFile
                        myStep.approve()
                        isUpdated = True
                elif myStep.type == "4":
                    myStep.date = step.date
                    myStep.uploadedFile = step.uploadedFile
                    if myStep.date and myStep.uploadedFile:
                        myStep.approve()
                        isUpdated = True
                elif myStep.type == "5":
                    myStep.checklist = step.checklist
                    isApproved = True
                    isUpdated = True
                    for check in myStep.checklist:
                        if not check.checked:
                            isApproved = False
                    if isApproved:
                        myStep.approve()
                if isUpdated:
                    myStep.updatedAt = datetime.utcnow()
                    self.save()

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        service = ProjectService()
        # before create
        if not document.id:
            service.handlerProjectBeforeCreate(document)

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        service = ProjectService()
        # after create
        if 'created' in kwargs and kwargs['created']:
            service.handlerProjectAfterCreate(document)


signals.pre_save.connect(Project.pre_save, sender=Project)
signals.post_save.connect(Project.post_save, sender=Project)
