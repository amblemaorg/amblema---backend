# /app/models/learning_module_model.py


from datetime import datetime
from bson.objectid import ObjectId
import logging

from mongoengine import signals
from flask import current_app
from mongoengine import (
    EmbeddedDocument,
    Document,
    StringField,
    ListField,
    URLField,
    BooleanField,
    IntField,
    DateTimeField,
    ReferenceField,
    EmbeddedDocumentListField)
from marshmallow import (
    Schema, fields, pre_load, post_load, EXCLUDE, validate)

from app.helpers.ma_schema_fields import MAImageField, MAReferenceField
from app.helpers.ma_schema_validators import (
    not_blank, validate_image, validate_video)
from app.helpers.error_helpers import RegisterNotFound


class Quiz(Document):
    module = ReferenceField('LearningModule')
    question = StringField(required=True)
    optionA = StringField(required=True)
    optionB = StringField(required=True)
    optionC = StringField(required=True)
    optionD = StringField(required=True)
    correctOption = StringField(required=True)
    status = BooleanField(default=True)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'quizzes'}

    def clean(self):
        self.updatedAt = datetime.utcnow()


class LearningModule(Document):
    title = StringField(required=True)
    description = StringField(required=True)
    secondaryTitle = StringField(required=True)
    secondaryDescription = StringField(required=True)
    objectives = ListField(StringField(), required=True)
    images = ListField(URLField(), required=True)
    videos = ListField(URLField(), required=True)
    duration = IntField(required=True, min_value=0)
    points = IntField(required=True, min_value=0)
    status = BooleanField(default=True)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)
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
            if not document.status:
                Quiz.objects(
                    module=str(document.id),
                    status=True).update(set__status=False)

    def getQuizzes(self):
        return Quiz.objects(module=self, status=True).all()

    def evaluate(self, answers):
        """
        Check if the answers given are incorrects  
        answers : {'quizId':str, 'option':str(1-4)}

        Return all incorrects answers
        Otherwise return false
        """
        incorrectAnswers = []
        for quiz in self.getQuizzes():

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


"""        
SCHEMAS FOR MODELS 
"""


class QuizSchema(Schema):
    id = fields.Str(dump_only=True)
    module = MAReferenceField(required=True, field='title')
    question = fields.Str(required=True, validate=not_blank)
    optionA = fields.Str(required=True, validate=not_blank)
    optionB = fields.Str(required=True, validate=not_blank)
    optionC = fields.Str(required=True, validate=not_blank)
    optionD = fields.Str(required=True, validate=not_blank)
    correctOption = fields.Str(
        required=True,
        validate=validate.OneOf(
            ["optionA", "optionB", "optionC", "optionD"],
            ["optionA", "optionB", "optionC", "optionD"]))
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if "module" in data:
            module = ""
            module = LearningModule.objects(
                id=data["module"], status=True).first()
            if not module:
                raise RegisterNotFound(message="Module not found",
                                       status_code=404,
                                       payload={"id": data['module']})
            data['module'] = module
        return data

    class Meta:
        unknown = EXCLUDE
        ordered = True


class LearningModuleSchema(Schema):
    id = fields.Str(dump_only=True)
    title = fields.Str(required=True, validate=not_blank)
    description = fields.Str(required=True, validate=not_blank)
    secondaryTitle = fields.Str(required=True, validate=not_blank)
    secondaryDescription = fields.Str(required=True, validate=not_blank)
    objectives = fields.List(fields.String(validate=not_blank))
    images = fields.List(
        MAImageField(
            validate=(not_blank, validate_image),
            folder='learningmodules'
        ),
        required=True,
        validate=not_blank)
    videos = fields.List(
        fields.Url(validate=(not_blank, validate_video)),
        required=True,
        validate=not_blank)
    duration = fields.Int(required=True, validate=validate.Range(min=0))
    points = fields.Int(required=True, validate=validate.Range(min=0))
    quizzes = fields.List(fields.Nested(QuizSchema()), dump_only=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True
