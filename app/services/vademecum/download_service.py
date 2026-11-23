# -*- coding: utf-8 -*-
# app/services/vademecum/download_service.py
"""Descarga protegida de fichas y su registro (API-14, GES-02 4.3 y 5.8).

Acceso: matrícula vigente > autorización del año > redescarga de lo ya bajado > 403. La
matrícula se calcula en cada descarga y la escuela queda como foto en el registro. Volver a
bajar la misma ficha en el mismo año es redescarga y no suma en `downloadCount`.
Sin acceso vigente (API-06, GES-02 4.3-3), una ficha que la cuenta ya bajó se entrega siempre
como redescarga, con el origen y la escuela de la descarga original y el año vigente: nunca
suma en `downloadCount` ni en los indicadores.
"""

import logging
import os
import re

from flask import current_app
from mongoengine.errors import NotUniqueError

from app.models.state_model import State
from app.models.user_model import User
from app.models.vademecum import (
    DownloadAccount, DownloadSchool, DownloadSchoolYear, DownloadSheet, VademecumAuthorization,
    VademecumDownload, VademecumSheet)
from app.services.vademecum.account_service import error
from app.services.vademecum.catalog_service import CatalogService, not_found, object_id
from app.services.vademecum.enrollment_service import EnrollmentService

logger = logging.getLogger(__name__)

UNSAFE_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|\r\n\t]+')


class Delivery(object):
    """Descarga ya registrada: lo que el controlador necesita para responder el PDF."""

    def __init__(self, download, path, filename):
        self.download = download
        self.path = path
        self.filename = filename


def download_filename(sheet):
    name = u"{} {}".format(sheet.code or u"", sheet.title or u"").strip()
    name = UNSAFE_FILENAME_CHARS.sub(u" ", name)
    return u" ".join(name.split())[:150] + u".pdf"


def pdf_path(sheet):
    """Ruta absoluta del PDF dentro del almacenamiento, o None si no existe."""
    storage = current_app.config.get("VADEMECUM_STORAGE_PATH")
    if not storage or not sheet.file or not sheet.file.pdfPath:
        return None
    root = os.path.realpath(storage)
    path = os.path.realpath(os.path.join(root, sheet.file.pdfPath))
    if not path.startswith(root + os.sep) or not os.path.isfile(path):
        return None
    return path


class DownloadService(object):

    def __init__(self, enrollmentService=None):
        self.enrollment = enrollmentService or EnrollmentService()

    def download(self, account, sheetId, jsonData):
        """(Delivery, None) o (None, respuesta de error)."""
        sheet = CatalogService().published_sheet(sheetId)
        if not sheet:
            return None, not_found()

        schoolYear = self.enrollment.current_school_year()
        if not schoolYear:
            return None, error("general", "117", "No current school year", 409)

        schoolId = (jsonData or {}).get("schoolId")
        if schoolId is not None and not isinstance(schoolId, str):
            return None, error("schoolId", "110", "School does not match enrollment")

        enrollment = self.enrollment.resolve(account.email, schoolYear)
        school = None
        if enrollment.is_enrolled:
            # La matrícula tiene prioridad sobre la autorización (GES-02 4.3)
            origin = "enrollment"
            if schoolId:
                school = enrollment.school(schoolId)
                if not school:
                    return None, error("schoolId", "110", "School does not match enrollment")
            elif len(enrollment.schools) == 1:
                school = enrollment.schools[0]
            else:
                return None, error("schoolId", "109", "School is required")
        elif VademecumAuthorization.objects(account=account.id, schoolYear=schoolYear.id,
                                            revokedAt=None).first():
            origin = "external"
        else:
            # Sin acceso vigente solo se entrega lo que la cuenta ya bajó alguna vez
            original = self._original_download(account, sheet)
            if not original:
                return None, error("general", "108", "No access to new sheets", 403)
            path = pdf_path(sheet)
            if not path:
                logger.error("Vademecum: PDF missing for published sheet %s", sheet.id)
                return None, not_found()
            download = self._record(account, sheet, schoolYear, original.origin, original.school,
                                    original.teacherId, forceRedownload=True)
            return Delivery(download, path, download_filename(sheet)), None

        path = pdf_path(sheet)
        if not path:
            # Ficha publicada sin archivo en disco: no se registra una descarga fallida
            logger.error("Vademecum: PDF missing for published sheet %s", sheet.id)
            return None, not_found()

        download = self._record(account, sheet, schoolYear, origin,
                                self._school_snapshot(school) if school else None,
                                enrollment.teacherIds.get(school["id"]) if school else None)
        return Delivery(download, path, download_filename(sheet)), None

    def _original_download(self, account, sheet):
        """La descarga con acceso más reciente de esta ficha (en cualquier año), o None."""
        return VademecumDownload.objects(
            __raw__={"account.id": str(account.id), "sheet.id": str(sheet.id),
                     "isRedownload": False}).order_by("-createdAt").first()

    def _record(self, account, sheet, schoolYear, origin, school, teacherId,
                forceRedownload=False):
        """`school`: DownloadSchool ya armada (o None). Con `forceRedownload` nunca cuenta."""
        def build(isRedownload):
            return VademecumDownload(
                sheet=self._sheet_snapshot(sheet),
                account=DownloadAccount(id=str(account.id), email=account.email,
                                        firstName=account.firstName, lastName=account.lastName),
                teacherId=teacherId,
                school=self._copy_school(school),
                schoolYear=DownloadSchoolYear(id=str(schoolYear.id), name=schoolYear.name),
                origin=origin,
                isRedownload=isRedownload)

        counted = forceRedownload or VademecumDownload.objects(
            __raw__={"account.id": str(account.id), "sheet.id": str(sheet.id),
                     "schoolYear.id": str(schoolYear.id), "isRedownload": False}).first()
        if not counted:
            download = build(isRedownload=False)
            try:
                download.save()
            except NotUniqueError:
                pass  # otra descarga simultánea ya contó: esta queda como redescarga
            else:
                VademecumSheet.objects(id=sheet.id).update_one(inc__downloadCount=1)
                return download
        download = build(isRedownload=True)
        download.save()
        return download

    def _copy_school(self, school):
        """Copia de la foto de la escuela: cada registro lleva su propia instancia."""
        if not school:
            return None
        return DownloadSchool(id=school.id, name=school.name, code=school.code,
                              stateId=school.stateId, stateName=school.stateName)

    def _sheet_snapshot(self, sheet):
        sheetType = sheet.sheetType
        return DownloadSheet(
            id=str(sheet.id), code=sheet.code, title=sheet.title,
            sheetTypeId=str(sheetType.id) if sheetType else None,
            sheetTypeName=sheetType.name if sheetType else None)

    def _school_snapshot(self, school):
        stateId = stateName = None
        raw = User._get_collection().find_one({"_id": object_id(school["id"])},
                                              {"addressState": 1})
        stateRef = (raw or {}).get("addressState")
        if stateRef:
            stateId = str(stateRef)
            state = State.objects(id=stateRef).only("name").first()
            stateName = state.name if state else None
        return DownloadSchool(id=school["id"], name=school.get("name"), code=school.get("code"),
                              stateId=stateId, stateName=stateName)
