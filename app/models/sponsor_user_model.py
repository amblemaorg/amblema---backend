# app/models/sponsor_user_model.py


from datetime import datetime

from mongoengine import fields

from app.models.user_model import User
from app.models.shared_embedded_documents import (
    ProjectReference, DocumentReference, SchoolReference)
from app.models.peca_yearbook_model import Entity


class SponsorUser(User):
    companyRif = fields.StringField(required=True)
    companyType = fields.StringField(required=True)
    companyOtherType = fields.StringField()
    companyPhone = fields.StringField(required=True)
    contactFirstName = fields.StringField()
    contactLastName = fields.StringField()
    contactEmail = fields.EmailField()
    contactPhone = fields.StringField()
    image = fields.URLField(null=True)
    webSite = fields.URLField()
    projects = fields.EmbeddedDocumentListField(ProjectReference)
    phase = fields.StringField(max_length=1, default="1")
    yearbook = fields.EmbeddedDocumentField(Entity, default=Entity())

    def findProject(self, projectId):
        project = self.projects.filter(id=projectId).first()
        if not project:
            return False
        return project

    def addProject(self, project):

        projectRef = ProjectReference(
            id=str(project.id),
            code=project.code.zfill(7),
            sponsor=DocumentReference(
                id=str(self.pk),
                name=self.name))
        if project.coordinator:
            projectRef.coordinator = DocumentReference(id=str(project.coordinator.id),
                                                       name=project.coordinator.name)
        if project.school:
            projectRef.school = SchoolReference(id=str(project.school.id),
                                                name=project.school.name,
                                                code=project.school.code)
        self.projects.append(projectRef)
        self.save()

    def updateProject(self, project):
        for myProject in self.projects:
            if myProject.id == str(project.id):
                if project.coordinator:
                    myProject.coordinator = DocumentReference(id=str(project.coordinator.id),
                                                              name=project.coordinator.name)
                if project.school:
                    myProject.school = DocumentReference(id=str(project.school.id),
                                                         name=project.school.name)
                self.save()
                break

    def removeProject(self, project):
        project = self.findProject(str(project.id))
        if project:
            self.projects.remove(project)
            self.save()
