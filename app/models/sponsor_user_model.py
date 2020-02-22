# app/models/sponsor_user_model.py


from datetime import datetime

from mongoengine import fields

from app.models.user_model import User
from app.models.shared_embedded_documents import (
    ProjectReference, DocumentReference)


class SponsorUser(User):
    firstName = fields.StringField(required=True)
    lastName = fields.StringField(required=True)
    cardType = fields.StringField(required=True)
    cardId = fields.StringField(required=True)
    companyRIF = fields.StringField(required=True)
    companyType = fields.StringField(required=True)
    companyOtherType = fields.StringField(required=False)
    companyPhone = fields.StringField(required=True)
    contactName = fields.StringField(required=True)
    contactPhone = fields.StringField(required=True)
    projects = fields.EmbeddedDocumentListField(ProjectReference)

    def clean(self):
        self.name = self.firstName + ' ' + self.lastName

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
            projectRef.school = DocumentReference(id=str(project.school.id),
                                                  name=project.school.name)
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
