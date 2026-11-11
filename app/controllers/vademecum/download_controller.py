# -*- coding: utf-8 -*-
# app/controllers/vademecum/download_controller.py
"""Descarga protegida: POST /vademecum/sheets/{sheetId}/download (API-14)."""

from flask import g, request, send_file
from flask_restful import Resource

from app.helpers.vademecum_auth import vademecum_teacher_required
from app.services.vademecum.download_service import DownloadService


class SheetDownloadController(Resource):
    @vademecum_teacher_required
    def post(self, sheetId):
        delivery, failure = DownloadService().download(
            g.vademecum_account, sheetId, request.get_json(silent=True))
        if failure:
            return failure
        response = send_file(delivery.path, mimetype="application/pdf", as_attachment=True,
                             attachment_filename=delivery.filename, cache_timeout=0)
        # El PDF es privado del docente: ningún proxy ni el navegador lo guarda en caché
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["X-Vademecum-Download-Id"] = str(delivery.download.id)
        response.headers["X-Vademecum-Redownload"] = (
            "true" if delivery.download.isRedownload else "false")
        return response
