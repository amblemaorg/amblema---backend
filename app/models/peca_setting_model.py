# app/models/peca_setting_model.py


from mongoengine import EmbeddedDocument, fields
from app.models.shared_embedded_documents import Link, CheckTemplate
from app.models.learning_module_model import Image
from app.models.activity_model import Activity


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


class LapsePlanning(EmbeddedDocument):
    proposalFundationFile = fields.EmbeddedDocumentField(
        Link, is_file=True)
    proposalFundationDescription = fields.StringField()
    meetingDescription = fields.StringField()


class AmbleCoins(EmbeddedDocument):
    teachersMeetingFile = fields.EmbeddedDocumentField(
        Link, is_file=True)
    teachersMeetingDescription = fields.StringField()
    piggyBankDescription = fields.StringField()
    piggyBankSlider = fields.EmbeddedDocumentListField(Image)


class AnnualConvention(EmbeddedDocument):
    step1Description = fields.StringField()
    step2Description = fields.StringField()
    step3Description = fields.StringField()
    step4Description = fields.StringField()


class Lapse1(EmbeddedDocument):
    initialWorkshop = fields.EmbeddedDocumentField(InitialWorshop)
    ambleCoins = fields.EmbeddedDocumentField(AmbleCoins)
    lapsePlanning = fields.EmbeddedDocumentField(LapsePlanning)
    annualConvention = fields.EmbeddedDocumentField(AnnualConvention)
    activities = fields.EmbeddedDocumentListField(Activity)


class Lapse2(EmbeddedDocument):
    lapsePlanning = fields.EmbeddedDocumentField(LapsePlanning)
    activities = fields.EmbeddedDocumentListField(Activity)


class Lapse3(EmbeddedDocument):
    lapsePlanning = fields.EmbeddedDocumentField(LapsePlanning)
    activities = fields.EmbeddedDocumentListField(Activity)


class PecaSetting(EmbeddedDocument):
    lapse1 = fields.EmbeddedDocumentField(Lapse1)
    lapse2 = fields.EmbeddedDocumentField(Lapse2)
    lapse3 = fields.EmbeddedDocumentField(Lapse3)
