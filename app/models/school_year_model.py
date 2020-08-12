# /app/models/school_year_model.py


from datetime import datetime

from mongoengine import (
    fields,
    Document,
    EmbeddedDocument)
from flask import current_app

from app.models.peca_setting_model import (
    PecaSetting,
    Lapse,
    InitialWorshop,
    LapsePlanning,
    AmbleCoins,
    AnnualConvention,
    AnnualPreparation,
    EnvironmentalProject,
    MathOlympic,
    SpecialLapseActivity)

from app.models.goal_setting_model import GoalSetting, GradeSetting
from app.models.monitoring_activity_model import MonitoringActivity
from app.models.shared_embedded_documents import Diagnostics


class SchoolYear(Document):
    name = fields.StringField(required=True)
    startDate = fields.DateField(default=datetime.utcnow)
    endDate = fields.DateField(default=datetime.utcnow)
    status = fields.StringField(required=True, default="1")
    pecaSetting = fields.EmbeddedDocumentField(PecaSetting)
    diagnostics = fields.EmbeddedDocumentField(
        Diagnostics, default=Diagnostics())
    nStudents = fields.IntField(default=0)
    nSchools = fields.IntField(default=0)
    nTeachers = fields.IntField(default=0)
    nSponsors = fields.IntField(default=0)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'school_years', 'ordering': ['+startDate']}

    def clean(self):
        self.updatedAt = datetime.utcnow()

    def initFirstPecaSetting(self):
        lapse = Lapse(
            initialWorkshop=InitialWorshop(),
            lapsePlanning=LapsePlanning(),
            ambleCoins=AmbleCoins(),
            annualConvention=AnnualConvention(),
            annualPreparation=AnnualPreparation(),
            mathOlympic=MathOlympic(),
            specialLapseActivity=SpecialLapseActivity(),
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
            environmentalProject=None,
            monitoringActivities=MonitoringActivity()
        )
        self.pecaSetting = pecaSetting

    def refreshDiagnosticsSummary(self):
        from app.models.peca_project_model import PecaProject

        summary = {}
        diagnosticsList = ['wordsPerMin',
                           'multiplicationsPerMin',
                           'operationsPerMin']
        for lapse in range(1, 4):
            summary['lapse{}'.format(lapse)] = {
                "wordsPerMinCount": 0,
                "wordsPerMinSum": 0,
                "wordsPerMinIndexSum": 0,
                "multiplicationsPerMinCount": 0,
                "multiplicationsPerMinSum": 0,
                "multiplicationsPerMinIndexSum": 0,
                "operationsPerMinCount": 0,
                "operationsPerMinSum": 0,
                "operationsPerMinIndexSum": 0
            }

        pecas = PecaProject.objects(schoolYear=self.pk, isDeleted=False)

        for peca in pecas:
            for lapse in range(1, 4):
                for diag in diagnosticsList:
                    if peca.school.diagnostics['lapse{}'.format(lapse)][diag]:
                        summary['lapse{}'.format(
                            lapse)]['{}Count'.format(diag)] += 1
                        summary['lapse{}'.format(
                            lapse)]['{}Sum'.format(diag)] += peca.school.diagnostics['lapse{}'.format(lapse)][diag]
                        summary['lapse{}'.format(
                            lapse)]['{}IndexSum'.format(diag)] += peca.school.diagnostics['lapse{}'.format(lapse)]['{}Index'.format(diag)]

        for i in range(1, 4):
            lapseSummary = summary['lapse{}'.format(i)]
            lapse = self.diagnostics['lapse{}'.format(i)]
            for diag in diagnosticsList:
                if lapseSummary['{}Count'.format(diag)]:
                    avg = round(lapseSummary['{}Sum'.format(diag)] /
                                lapseSummary['{}Count'.format(diag)], 3)
                    avgIndex = round(lapseSummary['{}IndexSum'.format(diag)] /
                                     lapseSummary['{}Count'.format(diag)], 3)
                    lapse[diag] = avg
                    lapse['{}Index'.format(diag)] = avgIndex
                else:
                    lapse[diag] = 0
                    lapse['{}Index'.format(diag)] = 0

        for diag in diagnosticsList:
            if self.diagnostics.lapse1[diag] and self.diagnostics.lapse2[diag] and self.diagnostics.lapse3[diag]:
                self.diagnostics.summary[diag] = round(
                    (
                        self.diagnostics.lapse1[diag]
                        + self.diagnostics.lapse2[diag]
                        + self.diagnostics.lapse3[diag]
                    ) / 3,
                    3)
                self.diagnostics.summary['{}Index'.format(diag)] = round(
                    (
                        self.diagnostics.lapse1['{}Index'.format(diag)]
                        + self.diagnostics.lapse2['{}Index'.format(diag)]
                        + self.diagnostics.lapse3['{}Index'.format(diag)]
                    ) / 3,
                    3)
            else:
                self.diagnostics.summary[diag] = 0
                self.diagnostics.summary['{}Index'.format(diag)] = 0
