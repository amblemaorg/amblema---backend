# /app/models/learning_module_model.py


from datetime import datetime
from bson.objectid import ObjectId
import logging

from mongoengine import signals
from flask import current_app
from mongoengine import (EmbeddedDocument, Document, fields)


class Image(EmbeddedDocument):
    url = fields.URLField(required=True)
    description = fields.StringField(required=True)


class Video(EmbeddedDocument):
    url = fields.URLField(required=True)
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
    title = fields.StringField(required=True)
    description = fields.StringField(required=True)
    secondaryTitle = fields.StringField(required=True)
    secondaryDescription = fields.StringField(required=True)
    objectives = fields.ListField(fields.StringField(), required=True)
    images = fields.EmbeddedDocumentListField(Image, required=True)
    videos = fields.EmbeddedDocumentListField(Video, required=True)
    duration = fields.IntField(required=True, min_value=0)
    points = fields.IntField(required=True, min_value=0)
    quizzes = fields.EmbeddedDocumentListField(Quiz, required=True)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'learning_modules'}

    def clean(self):
        self.updatedAt = datetime.utcnow()

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        current_app.logger.info('LearningModule POST_SAVE')
        if 'created' in kwargs and kwargs['created']:
            current_app.logger.info('After created')
        else:
            current_app.logger.info('After updated')

    def evaluate(self, answers):
        """
        Check if the answers given are incorrects  
        answers : {'quizId':str, 'option':str(1-4)}

        Return all incorrects answers
        Otherwise return false
        """
        incorrectAnswers = []
        for quiz in self.quizzes:

            if (
                (str(quiz.id) not in answers) or
                (quiz.correctOption != str(answers[str(quiz.id)]))
            ):
                incorrectAnswers.append(str(quiz.id))
        if not incorrectAnswers:
            return False
        else:
            return incorrectAnswers


signals.post_save.connect(LearningModule.post_save, sender=LearningModule)
