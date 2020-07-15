# app/models/peca_setting_model.py


from mongoengine import EmbeddedDocument, fields
from app.models.shared_embedded_documents import Link, CheckTemplate
from app.models.learning_module_model import Image
from app.models.activity_model import Activity
from app.models.goal_setting_model import GoalSetting
from app.models.environmental_project_model import EnvironmentalProject
from app.models.monitoring_activity_model import MonitoringActivity


class InitialWorshop(EmbeddedDocument):
    name = fields.StringField(default="Taller inicial")
    description = fields.StringField(default="")
    # agreementFile = fields.EmbeddedDocumentField(
    #    Link, is_file=True)
    #agreementDescription = fields.StringField()
    # planningMeetingFile = fields.EmbeddedDocumentField(
    #    Link, is_file=True)
    #planningMeetingDescription = fields.StringField()
    # teachersMeetingFile = fields.EmbeddedDocumentField(
    #    Link, is_file=True)
    #teachersMeetingDescription = fields.StringField()
    status = fields.StringField(max_length=1, default="2")
    isStandard = fields.BooleanField(default=True)


class LapsePlanning(EmbeddedDocument):
    name = fields.StringField(default="Planificación de lapso")
    proposalFundationFile = fields.EmbeddedDocumentField(
        Link, is_file=True)
    proposalFundationDescription = fields.StringField()
    meetingDescription = fields.StringField()
    status = fields.StringField(max_length=1, default="2")
    isStandard = fields.BooleanField(default=True)


class AmbleCoins(EmbeddedDocument):
    name = fields.StringField(default="AmbLeMonedas")
    description = fields.StringField(default="")
    teachersMeetingFile = fields.EmbeddedDocumentField(
        Link, is_file=True)
    teachersMeetingDescription = fields.StringField()
    piggyBankDescription = fields.StringField()
    piggyBankSlider = fields.EmbeddedDocumentListField(Image)
    status = fields.StringField(max_length=1, default="2")
    isStandard = fields.BooleanField(default=True)


class AnnualPreparation(EmbeddedDocument):
    name = fields.StringField(default="Preparación anual")
    step1Description = fields.StringField()
    step2Description = fields.StringField()
    step3Description = fields.StringField()
    step4Description = fields.StringField()
    status = fields.StringField(max_length=1, default="2")
    isStandard = fields.BooleanField(default=True)


class AnnualConvention(EmbeddedDocument):
    name = fields.StringField(default="Convención anual")
    description = fields.StringField(default="")
    checklist = fields.EmbeddedDocumentListField(CheckTemplate)
    status = fields.StringField(max_length=1, default="2")
    isStandard = fields.BooleanField(default=True)


class MathOlympic(EmbeddedDocument):
    name = fields.StringField(default="Olimpíadas matemáticas")
    description = fields.StringField()
    webDescription = fields.StringField()
    file = fields.EmbeddedDocumentField(
        Link, is_file=True)
    date = fields.DateTimeField(null=True)
    status = fields.StringField(max_length=1, default="2")
    isStandard = fields.BooleanField(default=True)


class SpecialLapseActivity(EmbeddedDocument):
    name = fields.StringField(default="Actividad especial de lapso")
    description = fields.StringField(default="")
    status = fields.StringField(max_length=1, default="2")
    isStandard = fields.BooleanField(default=True)


class Lapse(EmbeddedDocument):
    initialWorkshop = fields.EmbeddedDocumentField(InitialWorshop)
    ambleCoins = fields.EmbeddedDocumentField(AmbleCoins)
    lapsePlanning = fields.EmbeddedDocumentField(LapsePlanning)
    annualConvention = fields.EmbeddedDocumentField(AnnualConvention)
    annualPreparation = fields.EmbeddedDocumentField(AnnualPreparation)
    mathOlympic = fields.EmbeddedDocumentField(MathOlympic)
    specialLapseActivity = fields.EmbeddedDocumentField(SpecialLapseActivity)
    activities = fields.EmbeddedDocumentListField(Activity)


class PecaSetting(EmbeddedDocument):
    lapse1 = fields.EmbeddedDocumentField(Lapse)
    lapse2 = fields.EmbeddedDocumentField(Lapse)
    lapse3 = fields.EmbeddedDocumentField(Lapse)
    environmentalProject = fields.EmbeddedDocumentField(EnvironmentalProject)
    goalSetting = fields.EmbeddedDocumentField(GoalSetting)
    monitoringActivities = fields.EmbeddedDocumentField(MonitoringActivity)
