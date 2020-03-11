# app/models/school_user_model.py


from datetime import datetime

from mongoengine import fields

from app.models.user_model import User
from app.models.shared_embedded_documents import ProjectReference, DocumentReference


class SchoolUser(User):
    code = fields.StringField(required=True)
    phone = fields.StringField(required=True)
    image = fields.URLField()
    schoolType = fields.StringField(max_length=1)
    principalFirstName = fields.StringField()
    principalLastName = fields.StringField()
    principalEmail = fields.EmailField()
    principalPhone = fields.StringField()
    subPrincipalFirstName = fields.StringField()
    subPrincipalLastName = fields.StringField()
    subPrincipalEmail = fields.EmailField()
    subPrincipalPhone = fields.StringField()
    nTeachers = fields.IntField()
    nAdministrativeStaff = fields.IntField()
    nLaborStaff = fields.IntField()
    nStudents = fields.IntField()
    nGrades = fields.IntField()
    nSections = fields.IntField()
    schoolShift = fields.StringField(max_length=1)
    project = fields.EmbeddedDocumentField(ProjectReference)
    phase = fields.StringField(max_length=1, default="1")

    def addProject(self, project):

        projectRef = ProjectReference(
            id=str(project.id),
            code=project.code.zfill(7),
            school=DocumentReference(
                id=str(self.pk),
                name=self.name))
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
