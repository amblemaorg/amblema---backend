# app/models/project_model.py


from datetime import datetime

from flask import current_app
from mongoengine import (
    Document,
    EmbeddedDocument,
    fields,
    signals)

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
        self.status = "3"

    def clean(self):
        self.updatedAt = datetime.utcnow()


class StepsProgress(EmbeddedDocument):
    general = fields.FloatField(default=0)
    school = fields.FloatField(default=0)
    sponsor = fields.FloatField(default=0)
    coordinator = fields.FloatField(default=0)
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
                nApprovedGeneral += 1 if step.status == "3" else 0
            if step.tag == "2":
                nCoordinator += 1
                nApprovedCoordinator += 1 if step.status == "3" else 0
            if step.tag == "3":
                nSponsor += 1
                nApprovedSponsor += 1 if step.status == "3" else 0
            if step.tag == "4":
                nSchool += 1
                nApprovedSchool += 1 if step.status == "3" else 0
        self.general = 100 if nGeneral == 0 else round(
            nApprovedGeneral/nGeneral, 4)*100
        self.school = 100 if nSchool == 0 else round(
            nApprovedSchool/nSchool, 4)*100
        self.sponsor = 100 if nSponsor == 0 else round(
            nApprovedSponsor/nSponsor, 4)*100
        self.coordinator = 100 if nCoordinator == 0 else round(
            nApprovedCoordinator/nCoordinator, 4)*100


class ResumeSchoolYear(EmbeddedDocument):
    id = fields.StringField()
    name = fields.StringField()
    status = fields.StringField(max_length=1)


class ResumePeca(EmbeddedDocument):
    pecaId = fields.StringField()
    schoolYear = fields.EmbeddedDocumentField(ResumeSchoolYear)
    createAt = fields.DateTimeField(default=datetime.utcnow)


class Project(Document):
    code = fields.SequenceField(required=True, value_decorator=str)
    school = fields.ReferenceField('SchoolUser')
    sponsor = fields.ReferenceField('SponsorUser')
    coordinator = fields.ReferenceField('CoordinatorUser')
    schoolYear = fields.LazyReferenceField('SchoolYear')
    schoolYears = fields.EmbeddedDocumentListField(ResumePeca)
    stepsProgress = fields.EmbeddedDocumentField(StepsProgress)
    phase = fields.StringField(max_length=1, default="1")
    status = fields.StringField(default='1')
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    isDeleted = fields.BooleanField(default=False)
    meta = {'collection': 'projects'}

    def checkStepApproval(self, step):
        if step.hasDate and not step.date:
            return False
        if step.hasUpload and not step.uploadedFile:
            return False
        if step.hasChecklist:
            for check in step.checklist:
                if not check.checked:
                    return False
        if step.approvalType == "1" and step.status != "3":
            return False
        return True

    def checkConfirm(self):
        if (
            self.stepsProgress.general == 100
            and self.stepsProgress.sponsor == 100
            and self.stepsProgress.coordinator == 100
            and self.stepsProgress.school == 100
        ):
            return True
        return False

    def updateStep(self, step):
        for myStep in self.stepsProgress.steps:
            if step.id == myStep.id:
                isUpdated = False
                if myStep.hasUpload:
                    if myStep.uploadedFile != step.uploadedFile:
                        myStep.uploadedFile = step.uploadedFile
                        isUpdated = True
                if myStep.hasChecklist:
                    if myStep.checklist != step.checklist:
                        myStep.checklist = step.checklist
                        isUpdated = True
                if myStep.hasDate:
                    if myStep.date != step.date:
                        myStep.date = step.date
                        isUpdated = True
                if myStep.approvalType == "1":
                    if myStep.status != step.status:
                        myStep.status = step.status
                        isUpdated = True

                if isUpdated:
                    if self.checkStepApproval(myStep):
                        myStep.approve()
                        self.stepsProgress.updateProgress()
                    myStep.updatedAt = datetime.utcnow()
                    self.save()
                    if self.checkConfirm():
                        self.createPeca()
                break

    def createPeca(self):
        service = ProjectService()
        return service.createPeca(self)

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
