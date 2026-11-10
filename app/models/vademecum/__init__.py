# -*- coding: utf-8 -*-
# app/models/vademecum/__init__.py
"""Modelos del módulo Vademécum. Importa todas las clases para registrarlas en MongoEngine."""

from app.models.vademecum.sheet_type_model import SheetSeries, VademecumSheetType
from app.models.vademecum.area_model import VademecumArea
from app.models.vademecum.upload_model import UploadPage, UploadCut, VademecumUpload
from app.models.vademecum.sheet_model import SheetFile, VademecumSheet
from app.models.vademecum.teacher_account_model import AccountToken, VademecumTeacherAccount
from app.models.vademecum.access_request_model import VademecumAccessRequest
from app.models.vademecum.authorization_model import VademecumAuthorization
from app.models.vademecum.download_model import (
    DownloadSheet, DownloadAccount, DownloadSchool, DownloadSchoolYear, VademecumDownload)
from app.models.vademecum.favorite_model import VademecumFavorite
from app.models.vademecum.rating_model import VademecumRating
from app.models.vademecum.site_content_model import VademecumSiteContent

VADEMECUM_MODELS = (
    VademecumSheetType,
    VademecumArea,
    VademecumUpload,
    VademecumSheet,
    VademecumTeacherAccount,
    VademecumAccessRequest,
    VademecumAuthorization,
    VademecumDownload,
    VademecumFavorite,
    VademecumRating,
    VademecumSiteContent,
)
