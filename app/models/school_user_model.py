# app/models/school_user_model.py


from datetime import datetime

from mongoengine import fields

from app.models.user_model import User
from app.models.shared_embedded_documents import ProjectReference, DocumentReference


class SchoolUser(User):
    code = fields.StringField(required=True)
    contactFirstName = fields.StringField(required=True)
    contactLastName = fields.StringField(required=True)
    contactEmail = fields.StringField(required=True)
    contactPhone = fields.StringField(required=True)
    contactFunction = fields.StringField(required=True)
    project = fields.EmbeddedDocumentField(ProjectReference)

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
