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
from app.models.school_year_model import SchoolYear
from app.models.step_model import Step
from app.models.shared_embedded_documents import Link


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
        current_app.logger.info('project pre_save')
        current_app.logger.info(document.id)
        if not document.id:
            year = SchoolYear.objects(status="1", isDeleted=False).first()
            if not year:
                raise ValidationError(
                    message="There is not an active school year")
            current_app.logger.info('Before created')
            if not (document.school or document.sponsor or document.coordinator):
                raise ValidationError(
                    message="At least an sponsor, school or coordinator is required")
            current_app.logger.info('before for')
            initialSteps = StepsProgress()
            steps = Step.objects(schoolYear=str(year.id)).all()
            current_app.logger.info('right before for')
            for step in steps:
                stepCtrl = StepControl(
                    id=str(step.id),
                    name=step.name,
                    type=step.type,
                    tag=step.tag,
                    text=step.text,
                    date=step.date,
                    file=step.file,
                    video=step.video,
                    createdAt=step.createdAt,
                    updatedAt=step.updatedAt
                )
                if step.type == "5":
                    for check in step.checklist:
                        stepCtrl.checklist.append(
                            CheckElement(name=check.name, id=check.id))
                initialSteps.steps.append(stepCtrl)
                current_app.logger.info('inside for')
            current_app.logger.info('outside created')
            document.stepsProgress = initialSteps
            document.schoolYear = year
        else:
            current_app.logger.info('before updated')

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        current_app.logger.info('project post_save')
        current_app.logger.info(kwargs)
        if 'created' in kwargs and kwargs['created']:
            if document.sponsor:
                document.sponsor.addProject(document)
            if document.coordinator:
                document.coordinator.addProject(document)
            if document.school:
                document.school.addProject(document)


signals.pre_save.connect(Project.pre_save, sender=Project)
signals.post_save.connect(Project.post_save, sender=Project)
