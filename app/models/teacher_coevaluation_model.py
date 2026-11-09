# -*- coding: utf-8 -*-
# app/models/teacher_coevaluation_model.py

from datetime import datetime

from mongoengine import Document, EmbeddedDocument, fields

from app.helpers.coevaluation_helper import (
    INSTRUMENT_VERSION, MIN_SCORE, MAX_SCORE, compute_results,
    STATUS_NOT_STARTED, STATUS_PENDING_TEACHER, STATUS_PENDING_COORDINATOR,
    STATUS_COMPLETED)


class CoevaluationTeacher(EmbeddedDocument):
    """Copia de los datos del docente (de SchoolUser.teachers) al momento de evaluar."""
    firstName = fields.StringField()
    lastName = fields.StringField()
    cardType = fields.StringField()
    cardId = fields.StringField()
    email = fields.StringField()
    phone = fields.StringField()


class CoevaluationCoordinator(EmbeddedDocument):
    id = fields.StringField()
    name = fields.StringField()


class TeacherCoevaluation(Document):
    """Una coevaluación por docente y por PECA (año escolar)."""
    pecaId = fields.StringField(required=True)
    schoolYearId = fields.StringField(required=True)
    schoolYearName = fields.StringField()
    schoolId = fields.StringField(required=True)
    schoolName = fields.StringField()
    schoolCode = fields.StringField()
    teacherId = fields.StringField(required=True)
    teacher = fields.EmbeddedDocumentField(CoevaluationTeacher)
    sections = fields.StringField(default="")
    coordinator = fields.EmbeddedDocumentField(CoevaluationCoordinator)
    instrumentVersion = fields.IntField(default=INSTRUMENT_VERSION)

    coordinatorScores = fields.ListField(
        fields.IntField(min_value=MIN_SCORE, max_value=MAX_SCORE), default=list)
    coordinatorSubmittedAt = fields.DateTimeField(null=True)
    coordinatorSubmittedBy = fields.StringField(null=True)

    teacherScores = fields.ListField(
        fields.IntField(min_value=MIN_SCORE, max_value=MAX_SCORE), default=list)
    teacherSubmittedAt = fields.DateTimeField(null=True)

    # Solo el hash SHA-256 del token vigente. Sin null=True a propósito: así
    # MongoEngine omite el campo cuando es None y el índice único sparse no
    # choca entre coevaluaciones sin enlace activo.
    tokenHash = fields.StringField()
    emailSentAt = fields.DateTimeField(null=True)
    emailSentTo = fields.StringField(null=True)
    emailSentCount = fields.IntField(default=0)

    averages = fields.ListField(fields.FloatField(), default=list)
    totalScore = fields.FloatField(null=True)
    percentage = fields.FloatField(null=True)
    level = fields.StringField(null=True)
    completedAt = fields.DateTimeField(null=True)

    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'teacher_coevaluations',
        'indexes': [
            {'fields': ['pecaId', 'teacherId'], 'unique': True},
            {'fields': ['tokenHash'], 'unique': True, 'sparse': True},
            'schoolYearId',
            'schoolId',
        ]
    }

    @property
    def status(self):
        hasTeacher = self.teacherSubmittedAt is not None
        hasCoordinator = self.coordinatorSubmittedAt is not None
        if hasTeacher and hasCoordinator:
            return STATUS_COMPLETED
        if hasCoordinator:
            return STATUS_PENDING_TEACHER
        if hasTeacher:
            return STATUS_PENDING_COORDINATOR
        return STATUS_NOT_STARTED

    def refreshResults(self):
        results = compute_results(self.teacherScores, self.coordinatorScores)
        if results:
            self.averages = results["averages"]
            self.totalScore = results["totalScore"]
            self.percentage = results["percentage"]
            self.level = results["level"]
            if not self.completedAt:
                self.completedAt = datetime.utcnow()
        else:
            self.averages = []
            self.totalScore = None
            self.percentage = None
            self.level = None

    def clean(self):
        self.refreshResults()
        self.updatedAt = datetime.utcnow()
