# app/models/peca_setting_model.py


from mongoengine import EmbeddedDocument, fields
from app.models.shared_embedded_documents import Link, CheckTemplate
from app.models.learning_module_model import Image
from app.models.activity_model import Activity
from app.models.goal_setting_model import GoalSetting
from app.models.environmental_project_model import EnvironmentalProject


class InitialWorshop(EmbeddedDocument):
    agreementFile = fields.EmbeddedDocumentField(
        Link, is_file=True)
    agreementDescription = fields.StringField()
    planningMeetingFile = fields.EmbeddedDocumentField(
        Link, is_file=True)
    planningMeetingDescription = fields.StringField()
    teachersMeetingFile = fields.EmbeddedDocumentField(
        Link, is_file=True)
    teachersMeetingDescription = fields.StringField()
    status = fields.StringField(max_length=1, default="2")


class LapsePlanning(EmbeddedDocument):
    proposalFundationFile = fields.EmbeddedDocumentField(
        Link, is_file=True)
    proposalFundationDescription = fields.StringField()
    meetingDescription = fields.StringField()
    status = fields.StringField(max_length=1, default="2")


class AmbleCoins(EmbeddedDocument):
    teachersMeetingFile = fields.EmbeddedDocumentField(
        Link, is_file=True)
    teachersMeetingDescription = fields.StringField()
    piggyBankDescription = fields.StringField()
    piggyBankSlider = fields.EmbeddedDocumentListField(Image)
    status = fields.StringField(max_length=1, default="2")


class AnnualConvention(EmbeddedDocument):
    step1Description = fields.StringField()
    step2Description = fields.StringField()
    step3Description = fields.StringField()
    step4Description = fields.StringField()
    status = fields.StringField(max_length=1, default="2")


class MathOlimpic(EmbeddedDocument):
    file = fields.EmbeddedDocumentField(
        Link, is_file=True)
    description = fields.StringField()
    status = fields.StringField(max_length=1, default="2")


class Lapse(EmbeddedDocument):
    initialWorkshop = fields.EmbeddedDocumentField(InitialWorshop)
    ambleCoins = fields.EmbeddedDocumentField(AmbleCoins)
    lapsePlanning = fields.EmbeddedDocumentField(LapsePlanning)
    annualConvention = fields.EmbeddedDocumentField(AnnualConvention)
    mathOlimpic = fields.EmbeddedDocumentField(MathOlimpic)
    activities = fields.EmbeddedDocumentListField(Activity)


class PecaSetting(EmbeddedDocument):
    lapse1 = fields.EmbeddedDocumentField(Lapse)
    lapse2 = fields.EmbeddedDocumentField(Lapse)
    lapse3 = fields.EmbeddedDocumentField(Lapse)
    environmentalProject = fields.EmbeddedDocumentField(EnvironmentalProject)
    goalSetting = fields.EmbeddedDocumentField(GoalSetting)
