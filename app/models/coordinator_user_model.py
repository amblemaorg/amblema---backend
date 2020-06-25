# app/models/coordinator_user_model.py


from datetime import datetime

from flask import current_app
from pymongo import UpdateOne
from mongoengine import fields, EmbeddedDocument, signals

from app.models.user_model import User
from app.models.shared_embedded_documents import (
    DocumentReference, ProjectReference, SchoolReference, Link)
from app.helpers.error_helpers import RegisterNotFound
from app.models.peca_yearbook_model import Entity


class Answer(EmbeddedDocument):
    quizId = fields.ObjectIdField(required=True)
    option = fields.StringField(required=True)


class Attempt(EmbeddedDocument):
    answers = fields.EmbeddedDocumentListField(Answer, required=True)
    status = fields.StringField(max_length=1)
    createdAt = fields.DateTimeField(default=datetime.utcnow)


class LearningMod(EmbeddedDocument):
    moduleId = fields.ObjectIdField(required=True)
    score = fields.FloatField()
    attempts = fields.EmbeddedDocumentListField(Attempt)
    status = fields.StringField(max_length=1, default="1")


class CoordinatorUser(User):
    firstName = fields.StringField(required=True)
    lastName = fields.StringField(required=True)
    cardType = fields.StringField(required=True)
    cardId = fields.StringField(required=True, unique_c=True)
    phone = fields.StringField(required=True)
    gender = fields.StringField(max_length=1)
    birthdate = fields.DateTimeField(required=True)
    projects = fields.EmbeddedDocumentListField(ProjectReference)
    homePhone = fields.StringField(required=True)
    addressHome = fields.StringField()
    profession = fields.StringField(null=True)
    isReferred = fields.BooleanField()
    referredName = fields.StringField(null=True)
    image = fields.StringField(null=True)
    learning = fields.EmbeddedDocumentListField(LearningMod)
    nCoins = fields.IntField(default=0)
    instructed = fields.BooleanField(required=True, default=False)
    curriculum = fields.EmbeddedDocumentField(Link)
    phase = fields.StringField(max_length=1, default="1")
    yearbook = fields.EmbeddedDocumentField(Entity, default=Entity())

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
            coordinator=DocumentReference(
                id=str(self.pk),
                name=self.name))
        if project.sponsor:
            projectRef.sponsor = DocumentReference(id=str(project.sponsor.id),
                                                   name=project.sponsor.name)
        if project.school:
            projectRef.school = SchoolReference(id=str(project.school.id),
                                                name=project.school.name,
                                                code=project.school.code)
        self.projects.append(projectRef)
        self.save()

    def updateProject(self, project):
        for myProject in self.projects:
            if myProject.id == str(project.id):
                if project.sponsor:
                    myProject.sponsor = DocumentReference(id=str(project.sponsor.id),
                                                          name=project.sponsor.name)
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

    def isInstructed(self):
        from app.models.learning_module_model import LearningModule

        modules = LearningModule.objects(isDeleted=False).only("id")
        for module in modules:
            approved = False
            for my_module in self.learning:
                if my_module.moduleId == module.id and my_module.status == "3":
                    approved = True
            if not approved:
                return False
        return True

    def updateProjectsOnceInstructed(self):
        from app.models.project_model import Project
        projectIds = [project.id for project in self.projects]
        projects = Project.objects(
            id__in=projectIds, status="1", isDeleted=False)
        for project in projects:
            for step in project.stepsProgress.steps:
                if step.devName == "corrdinatorCompleteTrainingModules":
                    step.approve()
                    step.updatedAt = datetime.utcnow()
                    project.stepsProgress.updateProgress()
                    project.save()
                    break

    def tryAnswerLearningModule(self, module, answers):
        """
        Method for answer a learning module.

        Params:
           module: LearningModule()
           answers: [{"quizId": "str", "option": "str"}]
        The score is:
        1st attempt 4 coins
        2nd attempt 3 coins
        3rd attepmt 2 coins
        4 o more attempts 1 coin
        """

        if not self.curriculum:
            raise RegisterNotFound(
                message="Curriculum not found, coordinator must complete this step",
                status_code=404,
                payload={})
        found = False
        for my_module in self.learning:
            if my_module.moduleId == module.id:
                found = True
                nAttempts = len(my_module.attempts)
                results = module.evaluate(answers)
                if results["approved"]:
                    my_module.status = "3"
                    self.nCoins += my_module.score
                    if self.isInstructed():
                        self.instructed = True
                        self.updateProjectsOnceInstructed()
                else:
                    my_module.score = 1 if nAttempts > 2 else my_module.score - 1
                    my_module.status = "2"
                attempt = Attempt(
                    answers=answers,
                    status="1" if results["approved"] else "2"
                )
                my_module.attempts.append(attempt)
                self.save()
                return results
        if not found:
            my_module = LearningMod(
                moduleId=module.id
            )
            results = module.evaluate(answers)
            if results["approved"]:
                my_module.score = 4
                my_module.status = "3"
                self.nCoins += my_module.score
            else:
                my_module.score = 3
                my_module.status = "2"
            attempt = Attempt(
                answers=answers,
                status="1" if results["approved"] else "2"
            )
            my_module.attempts.append(attempt)
            self.learning.append(my_module)
            if results["approved"] and self.isInstructed():
                self.instructed = True
                self.updateProjectsOnceInstructed()
            self.save()
            return results

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        # before update
        if document.id:
            oldDocument = document.__class__.objects.get(id=document.id)
            if (
                (document.instructed != oldDocument.instructed
                 or document.curriculum != oldDocument.curriculum)
                and document.status != "4"
            ):
                if document.instructed and document.curriculum:
                    document.status = "3"


signals.pre_save.connect(CoordinatorUser.pre_save, sender=CoordinatorUser)
