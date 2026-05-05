# app/models/peca_olympics_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields
from flask import current_app

from app.models.shared_embedded_documents import Link, Diagnostics
from app.models.peca_activity_yearbook_model import ActivityYearbook
from app.models.peca_student_model import Student
from app.models.goal_setting_model import GradeSetting


class TeacherLink(EmbeddedDocument):
    id = fields.StringField()
    firstName = fields.StringField()
    lastName = fields.StringField()


class Section(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    grade = fields.StringField(max_length=1)
    name = fields.StringField()
    diagnostics = fields.EmbeddedDocumentField(
        Diagnostics, default=Diagnostics())
    goals = fields.EmbeddedDocumentField(GradeSetting)
    image = fields.StringField(null=True)
    isDeleted = fields.BooleanField(default=False)
    students = fields.EmbeddedDocumentListField(Student)
    teacher = fields.EmbeddedDocumentField(TeacherLink)

    def refreshDiagnosticsSummary(self):

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

        for student in self.students.filter(isDeleted=False):
            for lapse in range(1, 4):
                lapse_data = student['lapse{}'.format(lapse)]
                if lapse_data is None: continue
                for diag in diagnosticsList:
                    val_diag = lapse_data[diag]
                    if val_diag is not None and val_diag != "":
                        summary['lapse{}'.format(
                            lapse)]['{}Count'.format(diag)] += 1
                        summary['lapse{}'.format(
                            lapse)]['{}Sum'.format(diag)] += float(val_diag)
                        
                        val_index = lapse_data['{}Index'.format(diag)]
                        val = val_index if (val_index is not None and val_index != "") else 0
                        summary['lapse{}'.format(
                            lapse)]['{}IndexSum'.format(diag)] += float(val)
        
        for i in range(1, 4):
            lapseSummary = summary['lapse{}'.format(i)]
            lapse = self.diagnostics['lapse{}'.format(i)]
            for diag in diagnosticsList:
                if lapseSummary['{}Count'.format(diag)]:
                    avg = round(lapseSummary['{}Sum'.format(diag)] /
                                lapseSummary['{}Count'.format(diag)], 2)
                    avgIndex = round(lapseSummary['{}IndexSum'.format(diag)] /
                                     lapseSummary['{}Count'.format(diag)], 2)
                    lapse[diag] = avg
                    lapse['{}Index'.format(diag)] = avgIndex
                    lapse['{}Count'.format(diag)] = lapseSummary['{}Count'.format(diag)]
                else:
                    lapse[diag] = None
                    lapse['{}Index'.format(diag)] = None
                    lapse['{}Count'.format(diag)] = 0

        for diag in diagnosticsList:
            if self.diagnostics.lapse1[diag] is not None and self.diagnostics.lapse2[diag] is not None and self.diagnostics.lapse3[diag] is not None:
                self.diagnostics.summary[diag] = round(
                    (
                        self.diagnostics.lapse1[diag]
                        + self.diagnostics.lapse2[diag]
                        + self.diagnostics.lapse3[diag]
                    ) / 3,
                    2)
                self.diagnostics.summary['{}Index'.format(diag)] = round(
                    (
                        self.diagnostics.lapse1['{}Index'.format(diag)]
                        + self.diagnostics.lapse2['{}Index'.format(diag)]
                        + self.diagnostics.lapse3['{}Index'.format(diag)]) / 3,
                    2)
            else:
                self.diagnostics.summary[diag] = None
                self.diagnostics.summary['{}Index'.format(diag)] = None

"""class SectionClass(Document):
    id = fields.ObjectIdField(default=fields.ObjectId)
    grade = fields.StringField(max_length=1)
    name = fields.StringField()
    image = fields.StringField(null=True)
    isDeleted = fields.BooleanField(default=False)
    students = fields.EmbeddedDocumentListField(StudentClass)
    teacher = fields.EmbeddedDocumentField(TeacherLink)"""