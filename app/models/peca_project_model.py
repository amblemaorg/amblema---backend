# app/models/peca_project_model.py


from datetime import datetime
from bson import ObjectId

from flask import current_app
from mongoengine import fields, Document, EmbeddedDocument, signals

from app.models.shared_embedded_documents import ProjectReference, ImageStatus


class Diagnostic(EmbeddedDocument):
    multitplicationsPerMin = fields.IntField()
    multitplicationsPerMinIndex = fields.FloatField()
    operationsPerMin = fields.IntField()
    operationsPerMinIndex = fields.FloatField()
    wordsPerMin = fields.IntField()
    wordsPerMinIndex = fields.FloatField()
    mathDate = fields.DateTimeField()
    readingDate = fields.DateTimeField()

    def calculateIndex(self, setting):
        if self.multitplicationsPerMin:
            self.multitplicationsPerMinIndex = self.multitplicationsPerMin / \
                setting.multitplicationsPerMin
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


class Teacher(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    firstName = fields.StringField()
    lastName = fields.StringField()
    cardType = fields.StringField(max_length=1)
    cardId = fields.StringField()
    gender = fields.StringField(max_length=1)
    email = fields.StringField()
    phone = fields.StringField()
    addressState = fields.ReferenceField('State')
    addressMunicipality = fields.ReferenceField('Municipality')
    address = fields.StringField()
    addressCity = fields.StringField()
    status = fields.StringField(max_length=1, default=1)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)


class TeacherLink(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
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
    teachers = fields.EmbeddedDocumentListField(Teacher)
    slider = fields.EmbeddedDocumentListField(ImageStatus)


class PecaProject(Document):
    schoolYear = fields.LazyReferenceField('SchoolYear')
    schoolYearName = fields.StringField()
    project = fields.EmbeddedDocumentField(ProjectReference)
    school = fields.EmbeddedDocumentField(School)
    isDeleted = fields.BooleanField(default=False)
