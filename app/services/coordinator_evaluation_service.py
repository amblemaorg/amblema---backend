# -*- coding: utf-8 -*-
# app/services/coordinator_evaluation_service.py
"""
Valoración / Opinión del Coordinador AmbLeMa HQS.

- El coordinador (o un administrador con permiso) responde 4 preguntas cerradas
  una sola vez por PECA (año escolar) desde PECA -> Datos de la escuela.
- El puntaje total (0-100) aporta el 20 % del Puntaje Global HQS.
"""

from datetime import datetime

from bson import ObjectId
from flask import current_app
from marshmallow import ValidationError
from mongoengine.errors import NotUniqueError

from app.models.peca_project_model import PecaProject
from app.models.coordinator_evaluation_model import (
    CoordinatorEvaluation, CoordinatorEvaluationCoordinator)
from app.schemas.coordinator_evaluation_schema import (
    CoordinatorAnswersSchema, answers_to_list)
from app.helpers.coordinator_evaluation_helper import (
    N_QUESTIONS, STATUS_COMPLETED, STATUS_NOT_STARTED, STATUS_LABELS,
    get_coordinator_instrument, get_option_label)
from app.helpers.handler_authorization import is_admin


PERMISSION = "teacher_coevaluation"
PECA_FIELDS = ('id', 'project', 'schoolYear', 'schoolYearName')


def _error(message, status_code, **extra):
    body = {"message": message}
    body.update(extra)
    return body, status_code


def _iso(value):
    return value.isoformat() if value else None


class CoordinatorEvaluationService():

    def _get_peca(self, pecaId):
        if not ObjectId.is_valid(pecaId):
            return None
        return PecaProject.objects(id=pecaId, isDeleted=False).only(*PECA_FIELDS).first()

    def _is_project_coordinator(self, caller, peca):
        coordinator = peca.project.coordinator if peca.project else None
        return bool(
            caller and caller.userType == "2" and coordinator
            and str(coordinator.id) == str(caller.id))

    def _can_view_scores(self, caller):
        if caller is None and current_app.config.get("TESTING"):
            return True
        return bool(caller and is_admin(caller))

    def check_access(self, caller, peca):
        """
        Lectura: admin (por rol) o coordinador del proyecto, y el rol debe tener
        el permiso teacher_coevaluation. En TESTING sin token no se valida.
        """
        if caller is None and current_app.config.get("TESTING"):
            return None
        if caller is None or not caller.role:
            return _error("No authorized", 403)
        if PERMISSION not in caller.get_permissions():
            return _error("No authorized", 403)
        if is_admin(caller) or self._is_project_coordinator(caller, peca):
            return None
        return _error("No authorized", 403)

    def check_submit_access(self, caller, peca):
        """Escritura: solo el coordinador asignado al proyecto (no admin)."""
        denied = self.check_access(caller, peca)
        if denied:
            return denied
        if caller is None and current_app.config.get("TESTING"):
            return None
        if not self._is_project_coordinator(caller, peca):
            return _error(u"Solo el coordinador asignado puede registrar esta valoración.", 403)
        return None

    def _validate_answers(self, jsonData):
        try:
            data = CoordinatorAnswersSchema().load(jsonData or {})
        except ValidationError as err:
            return None, (err.normalized_messages(), 400)
        return answers_to_list(data), None

    def _serialize_answers(self, evaluation, include_scores=True):
        answers = evaluation.answers if evaluation else []
        scores = evaluation.scores if evaluation else []
        items = []
        for index in range(N_QUESTIONS):
            option = answers[index] if len(answers) == N_QUESTIONS else None
            items.append({
                "number": index + 1,
                "option": option,
                "optionLabel": get_option_label(option),
                "score": (scores[index] if (include_scores and len(scores) == N_QUESTIONS) else None),
            })
        return items

    def _detail(self, peca, evaluation, caller=None):
        projectSchool = peca.project.school if peca.project else None
        projectCoordinator = peca.project.coordinator if peca.project else None
        status = evaluation.status if evaluation else STATUS_NOT_STARTED
        showScores = self._can_view_scores(caller)
        isCoordinator = (caller is None and current_app.config.get("TESTING")) or self._is_project_coordinator(caller, peca)
        coordinator = (
            {"id": evaluation.coordinator.id, "name": evaluation.coordinator.name}
            if evaluation and evaluation.coordinator
            else {
                "id": projectCoordinator.id if projectCoordinator else None,
                "name": projectCoordinator.name if projectCoordinator else None,
            }
        )
        return {
            "id": str(evaluation.id) if evaluation else None,
            "pecaId": str(peca.id),
            "instrument": get_coordinator_instrument(include_scores=showScores),
            "schoolYear": {
                "id": str(peca.schoolYear.id) if peca.schoolYear else None,
                "name": peca.schoolYearName,
            },
            "school": {
                "id": projectSchool.id if projectSchool else None,
                "name": evaluation.schoolName if evaluation else (projectSchool.name if projectSchool else None),
                "code": evaluation.schoolCode if evaluation else (projectSchool.code if projectSchool else None),
            },
            "coordinator": coordinator,
            "status": status,
            "statusLabel": STATUS_LABELS[status],
            "answers": self._serialize_answers(evaluation, include_scores=showScores),
            "totalScore": evaluation.totalScore if (evaluation and showScores) else None,
            "submittedAt": _iso(evaluation.submittedAt) if evaluation else None,
            "canEvaluate": status != STATUS_COMPLETED and isCoordinator,
            "showScores": showScores,
        }

    def get_evaluation(self, pecaId, caller=None):
        peca = self._get_peca(pecaId)
        if not peca:
            return _error("Peca project not found", 404, pecaId=pecaId)
        denied = self.check_access(caller, peca)
        if denied:
            return denied
        evaluation = CoordinatorEvaluation.objects(pecaId=str(peca.id)).first()
        return self._detail(peca, evaluation, caller=caller), 200

    def save_evaluation(self, pecaId, jsonData, caller=None):
        peca = self._get_peca(pecaId)
        if not peca:
            return _error("Peca project not found", 404, pecaId=pecaId)
        denied = self.check_submit_access(caller, peca)
        if denied:
            return denied
        answers, error = self._validate_answers(jsonData)
        if error:
            return error

        existing = CoordinatorEvaluation.objects(pecaId=str(peca.id)).first()
        if existing:
            return _error(u"La valoración del coordinador ya fue registrada.", 409)

        projectSchool = peca.project.school if peca.project else None
        projectCoordinator = peca.project.coordinator if peca.project else None
        evaluation = CoordinatorEvaluation(
            pecaId=str(peca.id),
            schoolYearId=str(peca.schoolYear.id) if peca.schoolYear else "",
            schoolYearName=peca.schoolYearName,
            schoolId=str(projectSchool.id) if projectSchool and projectSchool.id else "",
            schoolName=projectSchool.name if projectSchool else None,
            schoolCode=projectSchool.code if projectSchool else None,
            coordinator=CoordinatorEvaluationCoordinator(
                id=projectCoordinator.id if projectCoordinator else None,
                name=projectCoordinator.name if projectCoordinator else None),
            answers=answers,
            submittedAt=datetime.utcnow(),
            submittedBy=str(caller.id) if caller else None,
        )
        try:
            evaluation.save()
        except NotUniqueError:
            return _error(u"La valoración del coordinador ya fue registrada.", 409)

        return self._detail(peca, evaluation, caller=caller), 200
