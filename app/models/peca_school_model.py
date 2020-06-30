# app/models/peca_school_model.py

from datetime import datetime

from mongoengine import EmbeddedDocument, fields

from app.models.peca_section_model import Section
from app.models.shared_embedded_documents import Approval, ImageStatus, Diagnostics


class School(EmbeddedDocument):
    name = fields.StringField()
    code = fields.StringField()
    addressState = fields.ReferenceField('State')
    addressMunicipality = fields.ReferenceField('Municipality')
    address = fields.StringField()
    addressCity = fields.StringField()
    principalFirstName = fields.StringField()
    principalLastName = fields.StringField()
    principalEmail = fields.EmailField()
    principalPhone = fields.StringField()
    subPrincipalFirstName = fields.StringField(null=True)
    subPrincipalLastName = fields.StringField(null=True)
    subPrincipalEmail = fields.EmailField(null=True)
    subPrincipalPhone = fields.StringField(null=True)
    nTeachers = fields.IntField(default=0)
    nSections = fields.IntField(default=0)
    nGrades = fields.IntField(default=0)
    nStudents = fields.IntField(default=0)
    nAdministrativeStaff = fields.IntField(default=0)
    nLaborStaff = fields.IntField(default=0)
    facebook = fields.StringField(null=True)
    instagram = fields.StringField(null=True)
    twitter = fields.StringField(null=True)
    sections = fields.EmbeddedDocumentListField(Section)
    slider = fields.EmbeddedDocumentListField(ImageStatus)
    diagnostics = fields.EmbeddedDocumentField(
        Diagnostics, default=Diagnostics())
    isInApproval = fields.BooleanField(default=False)
    approvalHistory = fields.EmbeddedDocumentListField(Approval)

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

        for section in self.sections:
            for lapse in range(1, 4):
                for diag in diagnosticsList:
                    if section.diagnostics['lapse{}'.format(lapse)][diag]:
                        summary['lapse{}'.format(
                            lapse)]['{}Count'.format(diag)] += 1
                        summary['lapse{}'.format(
                            lapse)]['{}Sum'.format(diag)] += section.diagnostics['lapse{}'.format(lapse)][diag]
                        summary['lapse{}'.format(
                            lapse)]['{}IndexSum'.format(diag)] += section.diagnostics['lapse{}'.format(lapse)]['{}Index'.format(diag)]

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
