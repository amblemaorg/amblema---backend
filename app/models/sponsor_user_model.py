# app/models/sponsor_user_model.py


from datetime import datetime
from flask import current_app

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
    image = fields.StringField(null=True)
    webSite = fields.StringField()
    projects = fields.EmbeddedDocumentListField(ProjectReference)
    phase = fields.StringField(max_length=1, default="1")
    yearbook = fields.EmbeddedDocumentField(Entity, default=Entity())

    def findProject(self, projectId):
        project = self.projects.filter(id=projectId).first()
        if not project:
            return False
        return project

    def addProject(self, project):

        self.projects.append(project.getReference())
        self.save()

    def updateProject(self, project):
        for myProject in self.projects:
            if myProject.id == str(project.id):
                newProject = project.getReference()
                myProject.code = newProject.code
                myProject.school = newProject.school
                myProject.sponsor = newProject.sponsor
                myProject.coordinator = newProject.coordinator
                myProject.schoolYears = newProject.schoolYears
                self.save()
                break

    def removeProject(self, project):
        project = self.findProject(str(project.id))
        if project:
            self.projects.remove(project)
            self.save()
