# app/models/school_user_model.py


from datetime import datetime

from mongoengine import fields

from app.models.user_model import User
from app.models.shared_embedded_documents import ProjectReference, DocumentReference


class SchoolUser(User):
    code = fields.StringField(required=True)
    phone = fields.StringField(required=True)
    image = fields.URLField(null=True)
    schoolType = fields.StringField(null=True, max_length=1)
    principalFirstName = fields.StringField()
    principalLastName = fields.StringField()
    principalEmail = fields.EmailField()
    principalPhone = fields.StringField()
    subPrincipalFirstName = fields.StringField(null=True)
    subPrincipalLastName = fields.StringField(null=True)
    subPrincipalEmail = fields.EmailField(null=True)
    subPrincipalPhone = fields.StringField(null=True)
    nTeachers = fields.IntField(null=True)
    nAdministrativeStaff = fields.IntField(null=True)
    nLaborStaff = fields.IntField(null=True)
    nStudents = fields.IntField(null=True)
    nGrades = fields.IntField(null=True)
    nSections = fields.IntField(null=True)
    schoolShift = fields.StringField(max_length=1, null=True)
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
