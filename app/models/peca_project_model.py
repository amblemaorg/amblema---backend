# app/models/peca_project_model.py


from datetime import datetime
from bson import ObjectId

from flask import current_app
from mongoengine import fields, Document, EmbeddedDocument, signals

from app.models.shared_embedded_documents import ProjectReference
from app.models.peca_amblecoins_model import AmblecoinsPeca
from app.models.peca_olympics_model import Olympics
from app.models.peca_annual_preparation_model import AnnualPreparationPeca
from app.models.peca_annual_convention_model import AnnualConventionPeca
from app.models.peca_lapse_planning_model import LapsePlanningPeca
from app.models.peca_initial_workshop_model import InitialWorkshopPeca
from app.models.peca_activities_model import ActivityPeca
from app.models.peca_schedule_model import ScheduleActivity
from app.models.peca_yearbook_model import Yearbook
from app.models.special_activity_model import SpecialActivity
from app.models.peca_school_model import School


class Lapse(EmbeddedDocument):
    ambleCoins = fields.EmbeddedDocumentField(AmblecoinsPeca)
    olympics = fields.EmbeddedDocumentField(Olympics)
    annualPreparation = fields.EmbeddedDocumentField(AnnualPreparationPeca)
    annualConvention = fields.EmbeddedDocumentField(AnnualConventionPeca)
    lapsePlanning = fields.EmbeddedDocumentField(LapsePlanningPeca)
    initialWorkshop = fields.EmbeddedDocumentField(InitialWorkshopPeca)
    activities = fields.EmbeddedDocumentListField(ActivityPeca)
    specialActivity = fields.EmbeddedDocumentField(SpecialActivity)


class PecaProject(Document):
    schoolYear = fields.LazyReferenceField('SchoolYear')
    schoolYearName = fields.StringField()
    project = fields.EmbeddedDocumentField(ProjectReference)
    school = fields.EmbeddedDocumentField(School)
    lapse1 = fields.EmbeddedDocumentField(Lapse)
    lapse2 = fields.EmbeddedDocumentField(Lapse)
    lapse3 = fields.EmbeddedDocumentField(Lapse)
    schedule = fields.EmbeddedDocumentListField(ScheduleActivity)
    yearbook = fields.EmbeddedDocumentField(Yearbook, default=Yearbook())
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        from app.services.peca_project_service import PecaProjectService
        service = PecaProjectService()
        # before create
        if not document.id:
            service.initPecaSetting(document)

    def scheduleActivity(self, devName, subject, startTime, description):
        from app.models.peca_schedule_model import ScheduleActivity

        try:
            found = False
            for act in self.schedule:
                if act.devName == devName:
                    act.startDate = startTime
                    act.endTime = startTime
                    found = True
                    break
            if not found:
                self.schedule.append(
                    ScheduleActivity(
                        devName=devName,
                        subject=subject,
                        startTime=startTime,
                        endTime=startTime,
                        description=description
                    )
                )

        except Exception as e:
            return {'status': 0, 'message': str(e)}, 400


signals.pre_save.connect(PecaProject.pre_save, sender=PecaProject)
