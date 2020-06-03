# app/models/peca_project_model.py


from datetime import datetime
from bson import ObjectId

from flask import current_app
from mongoengine import fields, Document, EmbeddedDocument, signals

from app.models.shared_embedded_documents import ProjectReference, ImageStatus
from app.models.peca_amblecoins_model import AmblecoinsPeca
from app.models.peca_olympics_model import Olympics
from app.models.peca_annual_preparation_model import AnnualPreparationPeca
from app.models.peca_annual_convention_model import AnnualConventionPeca
from app.models.peca_lapse_planning_model import LapsePlanningPeca
from app.models.peca_initial_workshop_model import InitialWorkshopPeca
from app.models.peca_activities_model import ActivityPeca


class Diagnostic(EmbeddedDocument):
    multiplicationsPerMin = fields.IntField()
    multiplicationsPerMinIndex = fields.FloatField()
    operationsPerMin = fields.IntField()
    operationsPerMinIndex = fields.FloatField()
    wordsPerMin = fields.IntField()
    wordsPerMinIndex = fields.FloatField()
    mathDate = fields.DateTimeField()
    logicDate = fields.DateTimeField()
    readingDate = fields.DateTimeField()

    def calculateIndex(self, setting):
        if self.multiplicationsPerMin:
            self.multiplicationsPerMinIndex = self.multiplicationsPerMin / \
                setting.multiplicationsPerMin
        if self.operationsPerMin:
            self.operationsPerMinIndex = self.operationsPerMin / setting.operationsPerMin
        if self.wordsPerMin:
            self.wordsPerMinIndex = self.wordsPerMin / setting.wordsPerMin


class Student(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    firstName = fields.StringField()
    lastName = fields.StringField()
    cardId = fields.StringField()
    cardType = fields.StringField()
    birthdate = fields.DateTimeField()
    gender = fields.StringField(max_length=1)
    lapse1 = fields.EmbeddedDocumentField(Diagnostic)
    lapse2 = fields.EmbeddedDocumentField(Diagnostic)
    lapse3 = fields.EmbeddedDocumentField(Diagnostic)
    isDeleted = fields.BooleanField(default=False)


class TeacherLink(EmbeddedDocument):
    id = fields.StringField()
    firstName = fields.StringField()
    lastName = fields.StringField()


class Section(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    grade = fields.StringField(max_length=1)
    name = fields.StringField()
    isDeleted = fields.BooleanField(default=False)
    students = fields.EmbeddedDocumentListField(Student)
    teacher = fields.EmbeddedDocumentField(TeacherLink)


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
    subPrincipalFirstName = fields.StringField()
    subPrincipalLastName = fields.StringField()
    subPrincipalEmail = fields.EmailField()
    subPrincipalPhone = fields.StringField()
    nTeachers = fields.IntField()
    nGrades = fields.IntField()
    nStudents = fields.IntField()
    nAdministrativeStaff = fields.IntField()
    nLaborStaff = fields.IntField()
    facebook = fields.URLField()
    instagram = fields.StringField()
    twitter = fields.StringField()
    sections = fields.EmbeddedDocumentListField(Section)
    slider = fields.EmbeddedDocumentListField(ImageStatus)


class Lapse(EmbeddedDocument):
    ambleCoins = fields.EmbeddedDocumentField(AmblecoinsPeca)
    olympics = fields.EmbeddedDocumentField(Olympics)
    annualPreparation = fields.EmbeddedDocumentField(AnnualPreparationPeca)
    annualConvention = fields.EmbeddedDocumentField(AnnualConventionPeca)
    lapsePlanning = fields.EmbeddedDocumentField(LapsePlanningPeca)
    initialWorkshop = fields.EmbeddedDocumentField(InitialWorkshopPeca)
    activities = fields.EmbeddedDocumentListField(ActivityPeca)


class PecaProject(Document):
    schoolYear = fields.LazyReferenceField('SchoolYear')
    schoolYearName = fields.StringField()
    project = fields.EmbeddedDocumentField(ProjectReference)
    school = fields.EmbeddedDocumentField(School)
    lapse1 = fields.EmbeddedDocumentField(Lapse)
    lapse2 = fields.EmbeddedDocumentField(Lapse)
    lapse3 = fields.EmbeddedDocumentField(Lapse)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        from app.services.peca_project_service import PecaProjectService
        service = PecaProjectService()
        # before create
        if not document.id:
            service.initPecaSetting(document)


signals.pre_save.connect(PecaProject.pre_save, sender=PecaProject)
