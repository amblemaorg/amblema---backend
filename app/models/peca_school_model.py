# app/models/peca_school_model.py

from datetime import datetime

from mongoengine import EmbeddedDocument, fields

from app.models.peca_section_model import Section
from app.models.shared_embedded_documents import Approval, ImageStatus


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
    nTeachers = fields.IntField()
    nGrades = fields.IntField()
    nStudents = fields.IntField()
    nAdministrativeStaff = fields.IntField()
    nLaborStaff = fields.IntField()
    facebook = fields.StringField(null=True)
    instagram = fields.StringField(null=True)
    twitter = fields.StringField(null=True)
    sections = fields.EmbeddedDocumentListField(Section)
    slider = fields.EmbeddedDocumentListField(ImageStatus)
    isInApproval = fields.BooleanField(default=False)
    approvalHistory = fields.EmbeddedDocumentListField(Approval)
