# app/models/peca_project_model.py


from datetime import datetime

from flask import current_app
from mongoengine import fields, Document, EmbeddedDocument, signals

from app.models.shared_embedded_documents import ProjectReference


class School(EmbeddedDocument):
    name = fields.StringField()
    code = fields.StringField()
    addressState = fields.ReferenceField('State')
    addressMunicipality = fields.ReferenceField('Municipality')
    addressStreet = fields.StringField()
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


class PecaProject(Document):
    schoolYear = fields.LazyReferenceField('SchoolYear')
    schoolYearName = fields.StringField()
    project = fields.EmbeddedDocumentField(ProjectReference)
    school = fields.EmbeddedDocumentField(School)
    isDeleted = fields.BooleanField(default=False)
