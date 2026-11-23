# -*- coding: utf-8 -*-
# app/services/yearbook_download_service.py

from bson import ObjectId
from mongoengine.errors import DoesNotExist

from app.models.school_year_model import SchoolYear
from app.models.peca_project_model import PecaProject
from app.helpers.error_helpers import RegisterNotFound


class YearbookDownloadService():

    def listActive(self):
        schoolYear = SchoolYear.objects(status="1", isDeleted=False).first()
        if not schoolYear:
            return {"records": []}, 200
        pecas = PecaProject.objects(
            schoolYear=schoolYear.id, isDeleted=False
        ).only("id", "project", "yearbookDownloadEnabled")
        records = []
        for peca in pecas:
            if not peca.project:
                continue
            records.append({
                "projectId": str(peca.project.id),
                "pecaId": str(peca.id),
                "yearbookDownloadEnabled": bool(peca.yearbookDownloadEnabled)
            })
        return {"records": records}, 200

    def _load(self, pecaId):
        peca = None
        if ObjectId.is_valid(pecaId):
            peca = PecaProject.objects(id=pecaId, isDeleted=False).only(
                "id", "schoolYear", "yearbookDownloadEnabled").first()
        if not peca:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": pecaId})
        return peca

    def _isSchoolYearActive(self, peca):
        if not peca.schoolYear:
            return False
        try:
            schoolYear = peca.schoolYear.fetch()
        except DoesNotExist:
            return False
        return (not schoolYear.isDeleted) and schoolYear.status == "1"

    def get(self, pecaId):
        peca = self._load(pecaId)
        return {
            "pecaId": str(peca.id),
            "schoolYearActive": self._isSchoolYearActive(peca),
            "yearbookDownloadEnabled": bool(peca.yearbookDownloadEnabled)
        }, 200

    def setEnabled(self, pecaId, jsonData):
        if not isinstance(jsonData, dict):
            jsonData = {}
        value = jsonData.get("yearbookDownloadEnabled")
        if not isinstance(value, bool):
            return {"msg": "yearbookDownloadEnabled debe ser booleano"}, 400
        peca = self._load(pecaId)
        if not self._isSchoolYearActive(peca):
            return {"msg": "Solo se puede cambiar en el año escolar en curso"}, 400
        PecaProject.objects(id=pecaId).update_one(
            set__yearbookDownloadEnabled=value)
        return self.get(pecaId)
