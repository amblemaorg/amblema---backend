# /app/models/school_year_model.py


from datetime import datetime

from mongoengine import (
    fields,
    Document,
    EmbeddedDocument)

from app.models.peca_setting_model import (
    PecaSetting,
    Lapse,
    InitialWorshop,
    LapsePlanning,
    AmbleCoins,
    AnnualConvention,
    EnvironmentalProject,
    MathOlimpic)

from app.models.goal_setting_model import GoalSetting, GradeSetting


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
        lapse = Lapse(
            initialWorkshop=InitialWorshop(),
            lapsePlanning=LapsePlanning(),
            ambleCoins=AmbleCoins(),
            annualConvention=AnnualConvention(),
            mathOlimpic=MathOlimpic(),
            activities=[]
        )

        goalSetting = GoalSetting()
        for i in range(6):
            goalSetting['grade'+str(i+1)] = GradeSetting(
                multiplicationsPerMin=1,
                operationsPerMin=1,
                wordsPerMin=1
            )

        pecaSetting = PecaSetting(
            lapse1=lapse,
            lapse2=lapse,
            lapse3=lapse,
            goalSetting=goalSetting,
            environmentalProject=EnvironmentalProject()
        )
        self.pecaSetting = pecaSetting
