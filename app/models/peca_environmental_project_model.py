# app/models/peca_environmental_project_model.py


from datetime import datetime

from mongoengine import fields, EmbeddedDocument, EmbeddedDocumentField
from marshmallow import ValidationError
from flask import current_app

from app.models.shared_embedded_documents import CheckElement


class Level(EmbeddedDocument):
    label = fields.StringField(max_length=1)
    value = fields.BooleanField(default=False)


class LevelDetail(EmbeddedDocument):
    target = fields.EmbeddedDocumentListField(Level)
    #week = fields.ListField(fields.DateTimeField(), max_length=2)
    duration = fields.IntField(min_value=0)
    techniques = fields.ListField(fields.StringField())
    activities = fields.EmbeddedDocumentListField(CheckElement)
    resources = fields.ListField(fields.StringField())
    evaluations = fields.ListField(fields.StringField())
    supportMaterial = fields.ListField(fields.URLField())


class Topic(EmbeddedDocument):
    name = fields.StringField()
    objectives = fields.ListField(fields.StringField())
    strategies = fields.ListField(fields.StringField())
    contents = fields.ListField(fields.StringField())
    levels = fields.EmbeddedDocumentListField(LevelDetail, max_length=7)


class Lapse(EmbeddedDocument):
    generalObjective = fields.StringField()
    topics = fields.EmbeddedDocumentListField(Topic, max_length=7)


class EnvironmentalProjectPeca(EmbeddedDocument):
    name = fields.StringField()
    description = fields.StringField(default="")
    lapse1 = fields.EmbeddedDocumentField(Lapse, null=True)
    lapse2 = fields.EmbeddedDocumentField(Lapse)
    lapse3 = fields.EmbeddedDocumentField(Lapse)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)

    def validateTarget(self):

        lapses = []
        if self.lapse1:
            lapses.append(self.lapse1)
        if self.lapse2:
            lapses.append(self.lapse2)
        if self.lapse3:
            lapses.append(self.lapse3)
        for lapse in lapses:
            for topic in lapse.topics:
                targets = []
                for level in topic.levels:
                    for target in level.target:
                        if target.value and target.label in targets:
                            raise ValidationError(
                                {"level": [{"status": "5",
                                            "msg": "Duplicated level target"}]}
                            )
                        elif target.value:
                            targets.append(target.label)
