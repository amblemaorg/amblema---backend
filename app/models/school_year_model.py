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
from app.models.shared_embedded_documents import Diagnostics, OlympicsSummary


class SchoolYear(Document):
    name = fields.StringField(required=True)
    startDate = fields.DateField(default=datetime.utcnow)
    endDate = fields.DateField(default=datetime.utcnow)
    status = fields.StringField(required=True, default="1")
    pecaSetting = fields.EmbeddedDocumentField(PecaSetting)
    diagnostics = fields.EmbeddedDocumentField(
        Diagnostics, default=Diagnostics())
    olympicsSummary = fields.EmbeddedDocumentField(
        OlympicsSummary, default=OlympicsSummary())
    nStudents = fields.IntField(default=0)
    nSchools = fields.IntField(default=0)
    nTeachers = fields.IntField(default=0)
    nSponsors = fields.IntField(default=0)
    nCoordinators = fields.IntField(default=0)
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

        pecas = PecaProject.objects(schoolYear=self.pk, isDeleted=False).only(
            "school", "lapse1", "lapse2", "lapse3")

        for peca in pecas:
            for lapse in range(1, 4):
                for diag in diagnosticsList:
                    if peca.school.diagnostics['lapse{}'.format(lapse)][diag] is not None:
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
                    lapse[diag] = None
                    lapse['{}Index'.format(diag)] = None

        for diag in diagnosticsList:
            if self.diagnostics.lapse1[diag] is not None and self.diagnostics.lapse2[diag] is not None and self.diagnostics.lapse3[diag] is not None:
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
                self.diagnostics.summary[diag] = None
                self.diagnostics.summary['{}Index'.format(diag)] = None

    def refreshOlympicsSummary(self):
        from app.models.peca_project_model import PecaProject

        res = {
            'mathEnrolledCount': 0,
            'mathParticipant': 0,
            'mathClassified': 0,
            'mathMedalsGold': 0,
            'mathMedalsSilver': 0,
            'mathMedalsBronze': 0,
            'mathParticipantRegional': 0,
            'mathClassifiedRegional': 0,
            'mathMedalsGoldNational': 0,
            'mathMedalsSilverNational': 0,
            'mathMedalsBronzeNational': 0,
            'readingEnrolledCount': 0,
            'readingParticipant': 0,
            'readingClassified': 0,
            'readingMedalsGold': 0,
            'readingMedalsSilver': 0,
            'readingMedalsBronze': 0,
            'readingParticipantRegional': 0,
            'readingClassifiedRegional': 0,
            'readingMedalsGoldNational': 0,
            'readingMedalsSilverNational': 0,
            'readingMedalsBronzeNational': 0
        }

        pecas = PecaProject.objects(schoolYear=self.pk, isDeleted=False).only(
            'lapse1.olympics.students',
            'lapse2.olympics.students',
            'lapse3.olympics.students',
            'lapse1.readingOlympics.students',
            'lapse2.readingOlympics.students',
            'lapse3.readingOlympics.students'
        )

        for peca in pecas:
            for lapse in range(1, 4):
                # Math
                olympics = peca['lapse{}'.format(lapse)].olympics
                if olympics:
                    for student in olympics.students:
                        res['mathEnrolledCount'] += 1
                        if student.status in ["2", "3"]:
                            res['mathParticipant'] += 1
                        if student.status == "3":
                            res['mathClassified'] += 1
                        
                        if student.statusRegional in ["1", "2"]:
                            res['mathParticipantRegional'] += 1
                        if student.statusRegional == "2":
                            res['mathClassifiedRegional'] += 1
                            if student.result == "1":
                                res['mathMedalsGold'] += 1
                            elif student.result == "2":
                                res['mathMedalsSilver'] += 1
                            elif student.result == "3":
                                res['mathMedalsBronze'] += 1
                        
                        if student.statusNational == "2":
                            if student.resultNational == "1":
                                res['mathMedalsGoldNational'] += 1
                            elif student.resultNational == "2":
                                res['mathMedalsSilverNational'] += 1
                            elif student.resultNational == "3":
                                res['mathMedalsBronzeNational'] += 1

                # Reading
                readingOlympics = peca['lapse{}'.format(lapse)].readingOlympics
                if readingOlympics:
                    for student in readingOlympics.students:
                        res['readingEnrolledCount'] += 1
                        if student.status in ["2", "3"]:
                            res['readingParticipant'] += 1
                        if student.status == "3":
                            res['readingClassified'] += 1

                        if student.statusRegional in ["1", "2"]:
                            res['readingParticipantRegional'] += 1
                        if student.statusRegional == "2":
                            res['readingClassifiedRegional'] += 1
                            if student.result == "1":
                                res['readingMedalsGold'] += 1
                            elif student.result == "2":
                                res['readingMedalsSilver'] += 1
                            elif student.result == "3":
                                res['readingMedalsBronze'] += 1
                        
                        if student.statusNational == "2":
                            if student.resultNational == "1":
                                res['readingMedalsGoldNational'] += 1
                            elif student.resultNational == "2":
                                res['readingMedalsSilverNational'] += 1
                            elif student.resultNational == "3":
                                res['readingMedalsBronzeNational'] += 1

        for field, value in res.items():
            self.olympicsSummary[field] = value