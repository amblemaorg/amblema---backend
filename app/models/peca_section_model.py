# app/models/peca_olympics_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields

from app.models.shared_embedded_documents import Link
from app.models.peca_activity_yearbook_model import ActivityYearbook
from app.models.peca_student_model import Student
from app.models.goal_setting_model import GradeSetting


class TeacherLink(EmbeddedDocument):
    id = fields.StringField()
    firstName = fields.StringField()
    lastName = fields.StringField()


class DiagnosticSummary(EmbeddedDocument):
    wordsPerMin = fields.IntField(default=0)
    wordsPerMinIndex = fields.FloatField(default=0)
    multiplicationsPerMin = fields.IntField(default=0)
    multiplicationsPerMinIndex = fields.FloatField(default=0)
    operationsPerMin = fields.IntField(default=0)
    operationsPerMinIndex = fields.FloatField(default=0)


class Diagnostics(EmbeddedDocument):
    lapse1 = fields.EmbeddedDocumentField(
        DiagnosticSummary, default=DiagnosticSummary())
    lapse2 = fields.EmbeddedDocumentField(
        DiagnosticSummary, default=DiagnosticSummary())
    lapse3 = fields.EmbeddedDocumentField(
        DiagnosticSummary, default=DiagnosticSummary())
    summary = fields.EmbeddedDocumentField(
        DiagnosticSummary, default=DiagnosticSummary())


class Section(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    grade = fields.StringField(max_length=1)
    name = fields.StringField()
    diagnostics = fields.EmbeddedDocumentField(
        Diagnostics, default=Diagnostics())
    goals = fields.EmbeddedDocumentField(GradeSetting)
    isDeleted = fields.BooleanField(default=False)
    students = fields.EmbeddedDocumentListField(Student)
    teacher = fields.EmbeddedDocumentField(TeacherLink)

    def refreshDiagnosticsSummary(self):

        summary = {}
        for lapse in range(1, 4):
            summary['lapse{}'.format(lapse)] = {
                "countWordsPerMin": 0,
                "sumWordsPerMin": 0,
                "countMultiplicationsPerMin": 0,
                "sumMultiplicationsPerMin": 0,
                "countOperationsPerMin": 0,
                "sumOperationsPerMin": 0
            }

        for student in self.students:
            for lapse in range(1, 4):
                if student['lapse{}'.format(lapse)]['wordsPerMin']:
                    summary['lapse{}'.format(lapse)]['countWordsPerMin'] += 1
                    summary['lapse{}'.format(
                        lapse)]['sumWordsPerMin'] += student['lapse{}'.format(lapse)]['wordsPerMin']
                if student['lapse{}'.format(lapse)]['multiplicationsPerMin']:
                    summary['lapse{}'.format(
                        lapse)]['countMultiplicationsPerMin'] += 1
                    summary['lapse{}'.format(
                        lapse)]['sumMultiplicationsPerMin'] += student['lapse{}'.format(lapse)]['multiplicationsPerMin']
                if student['lapse{}'.format(lapse)]['operationsPerMin']:
                    summary['lapse{}'.format(
                        lapse)]['countOperationsPerMin'] += 1
                    summary['lapse{}'.format(
                        lapse)]['sumOperationsPerMin'] += student['lapse{}'.format(lapse)]['operationsPerMin']

        for i in range(1, 4):
            lapseSummary = summary['lapse{}'.format(i)]
            lapse = self.diagnostics['lapse{}'.format(i)]
            if lapseSummary['countWordsPerMin']:
                avg = round(lapseSummary['sumWordsPerMin'] /
                            lapseSummary['countWordsPerMin'], 3)
                lapse.wordsPerMin = avg
                lapse.wordsPerMinIndex = round(avg / self.goals.wordsPerMin, 3)
            if lapseSummary['countMultiplicationsPerMin']:
                avg = round(lapseSummary['sumMultiplicationsPerMin'] /
                            lapseSummary['countMultiplicationsPerMin'], 3)
                lapse.multiplicationsPerMin = avg
                lapse.multiplicationsPerMinIndex = round(
                    avg / self.goals.multiplicationsPerMin, 3)
            if lapseSummary['countOperationsPerMin']:
                avg = round(lapseSummary['sumOperationsPerMin'] /
                            lapseSummary['countOperationsPerMin'], 3)
                lapse.operationsPerMin = avg
                lapse.operationsPerMinIndex = round(
                    avg / self.goals.operationsPerMin, 3)

        if self.diagnostics.lapse1.wordsPerMin and self.diagnostics.lapse2.wordsPerMin and self.diagnostics.lapse3.wordsPerMin:
            self.diagnostics.summary.wordsPerMin = round((self.diagnostics.lapse1.wordsPerMin
                                                          + self.diagnostics.lapse2.wordsPerMin
                                                          + self.diagnostics.lapse3.wordsPerMin) / 3, 3)
            self.diagnostics.summary.wordsPerMinIndex = round(self.diagnostics.summary.wordsPerMin /
                                                              self.goals.wordsPerMin, 3)
        if self.diagnostics.lapse1.multiplicationsPerMin and self.diagnostics.lapse2.multiplicationsPerMin and self.diagnostics.lapse3.multiplicationsPerMin:
            self.diagnostics.summary.multiplicationsPerMin = round((self.diagnostics.lapse1.multiplicationsPerMin
                                                                    + self.diagnostics.lapse2.multiplicationsPerMin
                                                                    + self.diagnostics.lapse3.multiplicationsPerMin) / 3, 3)
            self.diagnostics.summary.multiplicationsPerMinIndex = round(self.diagnostics.summary.multiplicationsPerMin /
                                                                        self.goals.multiplicationsPerMin, 3)
        if self.diagnostics.lapse1.operationsPerMin and self.diagnostics.lapse2.operationsPerMin and self.diagnostics.lapse3.operationsPerMin:
            self.diagnostics.summary.operationsPerMin = round((self.diagnostics.lapse1.operationsPerMin
                                                               + self.diagnostics.lapse2.operationsPerMin
                                                               + self.diagnostics.lapse3.operationsPerMin) / 3, 3)
            self.diagnostics.summary.operationsPerMinIndex = round(self.diagnostics.summary.operationsPerMin /
                                                                   self.goals.operationsPerMin, 3)
