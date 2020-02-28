# /app/models/school_year_model.py


from datetime import datetime

from mongoengine import (
    fields,
    Document,
    EmbeddedDocument)

from app.models.peca_setting_model import PecaSetting, Activities, InitialWorshop


class SchoolYear(Document):
    name = fields.StringField(required=True)
    startDate = fields.DateField(required=True)
    endDate = fields.DateField(required=True)
    status = fields.StringField(required=True, default="1")
    pecaSetting = fields.EmbeddedDocumentField(PecaSetting)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'school_years'}

    def clean(self):
        self.updatedAt = datetime.utcnow()

    def initFirstPecaSetting(self):
        initialWorkshop = InitialWorshop()
        activities = Activities(
            initialWorkshop=initialWorkshop
        )
        pecaSetting = PecaSetting(
            activities=activities
        )
        self.pecaSetting = pecaSetting
