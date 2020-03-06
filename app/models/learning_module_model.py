# /app/models/learning_module_model.py


from datetime import datetime
from bson.objectid import ObjectId
import logging

from pymongo import UpdateOne
from mongoengine import signals
from flask import current_app
from mongoengine import (EmbeddedDocument, Document, fields)


class SliderElement(EmbeddedDocument):
    url = fields.URLField()
    description = fields.StringField()
    type = fields.StringField(max_length=1)


class Image(EmbeddedDocument):
    image = fields.URLField(required=True)
    description = fields.StringField(required=True)


class Quiz(EmbeddedDocument):
    id = fields.ObjectIdField()
    question = fields.StringField(required=True)
    optionA = fields.StringField(required=True)
    optionB = fields.StringField(required=True)
    optionC = fields.StringField(required=True)
    optionD = fields.StringField(required=True)
    correctOption = fields.StringField(required=True)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)

    def clean(self):
        self.updatedAt = datetime.utcnow()
        if not self.id:
            self.id = ObjectId()


class LearningModule(Document):
    name = fields.StringField(required=True, unique_c=True)
    title = fields.StringField(required=True)
    description = fields.StringField(required=True)
    secondaryTitle = fields.StringField(required=True)
    secondaryDescription = fields.StringField(required=True)
    objectives = fields.ListField(fields.StringField(), required=True)
    slider = fields.EmbeddedDocumentListField(SliderElement)
    images = fields.EmbeddedDocumentListField(Image)
    duration = fields.IntField(required=True, min_value=0)
    quizzes = fields.EmbeddedDocumentListField(Quiz, required=True)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'learning_modules'}

    def clean(self):
        self.updatedAt = datetime.utcnow()

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        from app.models.coordinator_user_model import CoordinatorUser
        from app.models.project_model import Project
        if 'created' in kwargs and kwargs['created']:
            CoordinatorUser.objects(
                isDeleted=False,
                instructed=True, status__in=("2", "3")
            ).update(set__instructed=False, set__status="1")
            CoordinatorUser.objects(
                isDeleted=False,
                instructed=True
            ).update(set__instructed=False)

        else:
            if document.isDeleted:
                CoordinatorUser.objects(
                    isDeleted=False,
                    learning__moduleId=document.id
                ).update(pull__learning__moduleId=document.id)

    def evaluate(self, answers):
        """
        Check if the answers given are incorrects  
        answers : {'quizId':str, 'option':str(1-4)}

        Return all incorrects answers
        Otherwise return false
        """
        incorrectAnswers = []
        for quiz in self.quizzes:
            found = False
            for answer in answers:
                if str(quiz.id) == str(answer.quizId):
                    found = True
                    if quiz.correctOption != answer.option:
                        incorrectAnswers.append(str(answer.quizId))
            if not found:
                incorrectAnswers.append(str(quiz.id))
        if not incorrectAnswers:
            return {"approved": True}
        else:
            return {"approved": False, "incorrectAnswers": incorrectAnswers}


signals.post_save.connect(LearningModule.post_save, sender=LearningModule)
