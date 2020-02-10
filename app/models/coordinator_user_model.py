# app/models/coordinator_user_model.py


from datetime import datetime

from flask import current_app
from mongoengine import fields

from app.models.user_model import User
from app.models.shared_embedded_documents import (
    DocumentReference, ProjectReference)


class CoordinatorUser(User):
    firstName = fields.StringField(required=True)
    lastName = fields.StringField(required=True)
    cardType = fields.StringField(required=True)
    cardId = fields.StringField(required=True)
    birthdate = fields.DateField(required=True)
    projects = fields.EmbeddedDocumentListField(ProjectReference)
    homePhone = fields.StringField(required=True)
    addressHouse = fields.StringField()

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
            code=project.code,
            coordinator=DocumentReference(
                id=str(self.pk),
                name=self.name))
        if project.sponsor:
            projectRef.sponsor = DocumentReference(id=str(project.sponsor.id),
                                                   name=project.sponsor.name)
        if project.school:
            projectRef.school = DocumentReference(id=str(project.school.id),
                                                  name=project.school.name)
        self.projects.append(projectRef)
        self.save()

    def removeProject(self, project):
        project = self.findProject(str(project.id))
        if project:
            self.projects.remove(project)
            self.save()
