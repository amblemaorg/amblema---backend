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


class StepsProgress(EmbeddedDocument):
    general = fields.IntField(default=0)
    school = fields.IntField(default=0)
    sponsor = fields.IntField(default=0)
    coordinator = fields.IntField(default=0)


class Project(Document):
    code = fields.SequenceField(required=True, value_decorator=str)
    school = fields.ReferenceField('SchoolUser')
    sponsor = fields.ReferenceField('SponsorUser')
    coordinator = fields.ReferenceField('CoordinatorUser')
    schoolYear = fields.LazyReferenceField('SchoolYear')
    stepsProgress = fields.EmbeddedDocumentField(StepsProgress)
    state = fields.StringField(default='1')
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    status = fields.BooleanField(default=True)
    meta = {'collection': 'projects'}

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        current_app.logger.info('project pre_save')
        current_app.logger.info(kwargs)
        current_app.logger.info(document.id)
        if not document.id:
            year = SchoolYear.objects(state="1", status=True).first()
            if not year:
                raise ValidationError(
                    message="There is not an active school year")
            current_app.logger.info('Before created')
            if not (document.school or document.sponsor or document.coordinator):
                raise ValidationError(
                    message="At least an sponsor, school or coordinator is required")
            initialSteps = StepsProgress()
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
