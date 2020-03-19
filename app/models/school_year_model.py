# /app/models/school_year_model.py


from datetime import datetime

from mongoengine import (
    fields,
    Document,
    EmbeddedDocument)

from app.models.peca_setting_model import (
    PecaSetting, Lapse1, Lapse2, Lapse3, InitialWorshop, LapsePlanning, AmbleCoins, AnnualConvention)


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
        lapse1 = Lapse1(
            initialWorkshop=InitialWorshop(),
            lapsePlanning=LapsePlanning(),
            ambleCoins=AmbleCoins(),
            annualConvention=AnnualConvention()
        )
        lapse2 = Lapse2(
            lapsePlanning=LapsePlanning()
        )
        lapse3 = Lapse3(
            lapsePlanning=LapsePlanning()
        )
        pecaSetting = PecaSetting(
            lapse1=lapse1,
            lapse2=lapse2,
            lapse3=lapse3
        )
        self.pecaSetting = pecaSetting
