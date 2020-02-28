# app/models/peca_setting_model.py


from mongoengine import EmbeddedDocument, fields
from app.models.shared_embedded_documents import Link


class InitialWorshop(EmbeddedDocument):
    agreementFile = fields.EmbeddedDocumentField(
        Link, is_file=True, required=True)
    agreementDescription = fields.StringField(required=True)
    planningMeetingFile = fields.EmbeddedDocumentField(
        Link, is_file=True, required=True)
    planningMeetingDescription = fields.StringField(required=True)
    teachersMeetingFile = fields.EmbeddedDocumentField(
        Link, is_file=True, required=True)
    teachersMeetingDescription = fields.StringField(required=True)


"""class CustomActivity(EmbeddedDocument):
    name = fields.StringField()
    subtitle = fields.StringField()
    text = fields.StringField()
    slider = fields.EmbeddedDocumentField(Link)
    date = fields.DateTimeField()
    file = fields.EmbeddedDocumentField(Link, is_file=True)
"""


class Activities(EmbeddedDocument):
    initialWorkshop = fields.EmbeddedDocumentField(InitialWorshop)
    #customActivities = fields.EmbeddedDocumentListField(CustomActivity)


class PecaSetting(EmbeddedDocument):
    activities = fields.EmbeddedDocumentField(Activities)
