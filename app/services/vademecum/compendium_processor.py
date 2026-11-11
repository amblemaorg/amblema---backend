# -*- coding: utf-8 -*-
# app/services/vademecum/compendium_processor.py
"""Lectura del compendio original para proponer las fichas (GES-03 5.5).

API-08: abre el PDF, recorre las páginas e informa el avance.
API-09 completa la detección de encabezados y los cortes propuestos.
Requiere PyMuPDF (Python 3); el import es perezoso para no romper el arranque sin él.
"""

import os

from flask import current_app

from app.models.vademecum import UploadPage


class ProcessingError(Exception):
    """Fallo con un mensaje que el administrador puede entender (va a errorMessage)."""

    def __init__(self, message):
        super(ProcessingError, self).__init__(message)
        self.message = message


def original_path(upload):
    storage = current_app.config.get("VADEMECUM_STORAGE_PATH")
    if not storage or not upload.originalPath:
        raise ProcessingError(u"No se encontró el PDF original de la carga.")
    root = os.path.realpath(storage)
    path = os.path.realpath(os.path.join(root, upload.originalPath))
    if not path.startswith(root + os.sep) or not os.path.isfile(path):
        raise ProcessingError(u"No se encontró el PDF original de la carga.")
    return path


def open_pdf(path):
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ProcessingError(u"El servidor no tiene disponible la lectura de PDF.")
    try:
        document = fitz.open(path)
    except Exception:
        raise ProcessingError(u"El archivo está dañado o no es un PDF válido.")
    if document.needs_pass:
        document.close()
        raise ProcessingError(u"El PDF está protegido con contraseña.")
    if document.page_count == 0:
        document.close()
        raise ProcessingError(u"El PDF no tiene páginas.")
    return document


def process(upload, progress):
    """Devuelve pageCount, pages y proposedCuts; `progress(0..99)` informa el avance."""
    document = open_pdf(original_path(upload))
    try:
        total = document.page_count
        pages = []
        for index in range(total):
            pages.append(UploadPage(index=index))
            progress(int(99 * (index + 1) / total))
        return {"pageCount": total, "pages": pages, "proposedCuts": []}
    finally:
        document.close()
