# app/models/school_user_model.py


from datetime import datetime

from mongoengine import fields, EmbeddedDocument

from app.models.user_model import User
from app.models.shared_embedded_documents import ProjectReference, DocumentReference, SchoolReference, ImageStatus, Coordinate
from app.models.teacher_model import Teacher
from app.models.teacher_testimonial_model import TeacherTestimonial
from app.models.peca_yearbook_model import Entity


class OlympicsSummary(EmbeddedDocument):
    inscribed = fields.IntField(default=0)
    classified = fields.IntField(default=0)
    medalsGold = fields.IntField(default=0)
    medalsSilver = fields.IntField(default=0)
    medalsBronze = fields.IntField(default=0)


class SchoolUser(User):
    code = fields.StringField(required=True, unique_c=True)
    phone = fields.StringField(required=True)
    image = fields.StringField(null=True)
    schoolType = fields.StringField(null=True, max_length=1)
    addressZoneType = fields.StringField(max_length=1, null=True)
    addressZone = fields.StringField(null=True)
    coordinate = fields.PointField()
    principalFirstName = fields.StringField()
    principalLastName = fields.StringField()
    principalEmail = fields.EmailField()
    principalPhone = fields.StringField()
    subPrincipalFirstName = fields.StringField(null=True)
    subPrincipalLastName = fields.StringField(null=True)
    subPrincipalEmail = fields.EmailField(null=True)
    subPrincipalPhone = fields.StringField(null=True)
    nTeachers = fields.IntField(null=True, default=0)
    nAdministrativeStaff = fields.IntField(null=True, default=0)
    nLaborStaff = fields.IntField(null=True, default=0)
    nStudents = fields.IntField(null=True, default=0)
    nGrades = fields.IntField(null=True, default=0)
    nSections = fields.IntField(null=True, default=0)
    facebook = fields.StringField(default='', null=True)
    instagram = fields.StringField(default='', null=True)
    twitter = fields.StringField(default='', null=True)
    schoolShift = fields.StringField(max_length=1, null=True)
    project = fields.EmbeddedDocumentField(ProjectReference)
    teachers = fields.EmbeddedDocumentListField(Teacher)
    slider = fields.EmbeddedDocumentListField(ImageStatus)
    activitiesSlider = fields.ListField(fields.StringField())
    phase = fields.StringField(max_length=1, default="1")
    teachersTestimonials = fields.EmbeddedDocumentListField(
        TeacherTestimonial, max_length=4)
    yearbook = fields.EmbeddedDocumentField(Entity, default=Entity())
    historicalReview = fields.EmbeddedDocumentField(Entity, default=Entity())
    olympicsSummary = fields.EmbeddedDocumentField(
        OlympicsSummary, default=OlympicsSummary())

    def addProject(self, project):
        self.project = project.getReference()
        self.save()

    def updateProject(self, project):
        if self.project.id == str(project.id):
            self.project = project.getReference()
            self.save()

    def removeProject(self):
        self.project = None
        self.save()
