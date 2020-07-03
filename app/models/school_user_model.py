# app/models/school_user_model.py


from datetime import datetime

from mongoengine import fields, EmbeddedDocument

from app.models.user_model import User
from app.models.shared_embedded_documents import ProjectReference, DocumentReference, SchoolReference, ImageStatus, Coordinate
from app.models.teacher_model import Teacher
from app.models.teacher_testimonial_model import TeacherTestimonial
from app.models.peca_yearbook_model import Entity


class SchoolUser(User):
    code = fields.StringField(required=True, unique_c=True)
    phone = fields.StringField(required=True)
    image = fields.StringField(null=True)
    schoolType = fields.StringField(null=True, max_length=1)
    addressZoneType = fields.StringField(max_length=1, null=True)
    addressZone = fields.StringField(null=True)
    coordinate = fields.EmbeddedDocumentField(Coordinate)
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
    teachersTestimonials = fields.EmbeddedDocumentField(TeacherTestimonial)
    yearbook = fields.EmbeddedDocumentField(Entity, default=Entity())
    historicalReview = fields.EmbeddedDocumentField(Entity, default=Entity())

    def addProject(self, project):

        projectRef = ProjectReference(
            id=str(project.id),
            code=project.code.zfill(7),
            school=SchoolReference(
                id=str(self.pk),
                name=self.name,
                code=self.code))
        if project.coordinator:
            projectRef.coordinator = DocumentReference(id=str(project.coordinator.id),
                                                       name=project.coordinator.name)
        if project.sponsor:
            projectRef.sponsor = DocumentReference(id=str(project.sponsor.id),
                                                   name=project.sponsor.name)
        self.project = projectRef
        self.save()

    def updateProject(self, project):

        if self.project.id == str(project.id):
            if project.coordinator:
                self.project.coordinator = DocumentReference(id=str(project.coordinator.id),
                                                             name=project.coordinator.name)
            if project.sponsor:
                self.project.sponsor = DocumentReference(id=str(project.sponsor.id),
                                                         name=project.sponsor.name)
            self.save()

    def removeProject(self):
        self.project = None
        self.save()
