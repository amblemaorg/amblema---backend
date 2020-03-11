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


class StepFields(EmbeddedDocument):
    id = fields.StringField(required=True)
    name = fields.StringField(required=True)
    devName = fields.StringField(required=True)
    tag = fields.StringField(required=True, max_length=1)
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
    approvalType = fields.StringField(required=True, max_length=1)
    date = fields.DateTimeField(null=True)
    uploadedFile = fields.EmbeddedDocumentField(
        Link, is_file=True, null=True, default=None)
    isStandard = fields.BooleanField(default=False)
    status = fields.StringField(default="1", max_length=1)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'allow_inheritance': True}


class Approval(EmbeddedDocument):
    id = fields.StringField()
    comments = fields.StringField()
    status = fields.StringField(max_length=1)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)


class StepControl(StepFields):
    approvalHistory = fields.EmbeddedDocumentListField(Approval)

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

    def updateProgress(self):
        nGeneral = 0
        nSchool = 0
        nCoordinator = 0
        nSponsor = 0
        nApprovedGeneral = 0
        nApprovedSchool = 0
        nApprovedCoordinator = 0
        nApprovedSponsor = 0

        for step in self.steps:
            if step.tag == "1":
                nGeneral += 1
                nApprovedGeneral += 1 if step.status == "2" else 0
            if step.tag == "2":
                nCoordinator += 1
                nApprovedCoordinator += 1 if step.status == "2" else 0
            if step.tag == "3":
                nSponsor += 1
                nApprovedSponsor += 1 if step.status == "2" else 0
            if step.tag == "4":
                nSchool += 1
                nApprovedSchool += 1 if step.status == "2" else 0
        self.general = 100 if nGeneral == 0 else round(
            nApprovedGeneral/nGeneral, 4)*100
        self.school = 100 if nSchool == 0 else round(
            nApprovedSchool/nSchool, 4)*100
        self.sponsor = 100 if nSponsor == 0 else round(
            nApprovedSponsor/nSponsor, 4)*100
        self.coordinator = 100 if nCoordinator == 0 else round(
            nApprovedCoordinator/nCoordinator, 4)*100


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
                        if myStep.devName == "sponsorAgreementSchool":
                            for agreement in self.stepsProgress.steps:
                                if agreement.devName == "schoolAgreementSponsor":
                                    agreement.uploadedFile = step.uploadedFile
                                    agreement.approve()
                                    break
                        if myStep.devName == "schoolAgreementSponsor":
                            for agreement in self.stepsProgress.steps:
                                if agreement.devName == "sponsorAgreementSchool":
                                    agreement.uploadedFile = step.uploadedFile
                                    agreement.approve()
                                    break
                        if myStep.devName == "sponsorAgreementSchoolFoundation":
                            for agreement in self.stepsProgress.steps:
                                if agreement.devName == "schoolAgreementFoundation":
                                    agreement.uploadedFile = step.uploadedFile
                                    agreement.approve()
                                    break
                        if myStep.devName == "schoolAgreementFoundation":
                            for agreement in self.stepsProgress.steps:
                                if agreement.devName == "sponsorAgreementSchoolFoundation":
                                    agreement.uploadedFile = step.uploadedFile
                                    agreement.approve()
                                    break
                        if myStep.devName == "coordinatorSendCurriculum":
                            self.coordinator.curriculum = step.uploadedFile
                            self.coordinator.save()
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
                    self.stepsProgress.updateProgress()
                    self.save()
                break

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        service = ProjectService()
        # before create
        if not document.id:
            service.handlerProjectBeforeCreate(document)
        else:
            oldDocument = document.__class__.objects.get(id=document.id)
            service.handlerProjectBeforeUpdate(document, oldDocument)

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        service = ProjectService()
        # after create
        if 'created' in kwargs and kwargs['created']:
            service.handlerProjectAfterCreate(document)


signals.pre_save.connect(Project.pre_save, sender=Project)
signals.post_save.connect(Project.post_save, sender=Project)
