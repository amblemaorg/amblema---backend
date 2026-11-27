# -*- coding: utf-8 -*-
# app/models/coordinator_evaluation_model.py

from datetime import datetime

from mongoengine import Document, EmbeddedDocument, fields

from app.helpers.coordinator_evaluation_helper import (
    INSTRUMENT_VERSION, OPTION_CODES, STATUS_COMPLETED, STATUS_NOT_STARTED,
    compute_coordinator_results)


class CoordinatorEvaluationCoordinator(EmbeddedDocument):
    id = fields.StringField()
    name = fields.StringField()


class CoordinatorEvaluation(Document):
    """Valoración del coordinador sobre la escuela (una por PECA / año escolar)."""
    pecaId = fields.StringField(required=True)
    schoolYearId = fields.StringField(required=True)
    schoolYearName = fields.StringField()
    schoolId = fields.StringField(required=True)
    schoolName = fields.StringField()
    schoolCode = fields.StringField()
    coordinator = fields.EmbeddedDocumentField(CoordinatorEvaluationCoordinator)
    instrumentVersion = fields.IntField(default=INSTRUMENT_VERSION)

    answers = fields.ListField(fields.StringField(choices=OPTION_CODES), default=list)
    scores = fields.ListField(fields.FloatField(), default=list)
    totalScore = fields.FloatField(null=True)

    submittedAt = fields.DateTimeField(null=True)
    submittedBy = fields.StringField(null=True)

    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'coordinator_evaluations',
        'indexes': [
            {'fields': ['pecaId'], 'unique': True},
            'schoolYearId',
            'schoolId',
        ]
    }

    @property
    def status(self):
        return STATUS_COMPLETED if self.submittedAt is not None else STATUS_NOT_STARTED

    def refreshResults(self):
        results = compute_coordinator_results(self.answers)
        if results:
            self.scores = results["scores"]
            self.totalScore = results["totalScore"]
        else:
            self.scores = []
            self.totalScore = None

    def clean(self):
        self.refreshResults()
        self.updatedAt = datetime.utcnow()
