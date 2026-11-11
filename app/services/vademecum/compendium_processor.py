# -*- coding: utf-8 -*-
# app/services/vademecum/compendium_processor.py
"""Lectura del compendio original para proponer las fichas (GES-03 5.5).

API-08: abre el PDF, recorre las páginas e informa el avance.
API-09: lee el encabezado de cada página y propone los cortes (header_detection).
Requiere PyMuPDF (Python 3); el import es perezoso para no romper el arranque sin él.
"""

import os

from flask import current_app

from app.models.vademecum import UploadCut, UploadPage
from app.services.vademecum.header_detection import detect_header, propose_cuts

# El encabezado está arriba: solo se leen las líneas que empiezan en este tercio superior
HEADER_REGION = 0.3


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


def top_lines(page):
    """Líneas de texto del tercio superior, de arriba abajo y de izquierda a derecha."""
    limit = page.rect.y0 + page.rect.height * HEADER_REGION
    lines = []
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            x0, y0 = line["bbox"][0], line["bbox"][1]
            text = u"".join(span.get("text", u"") for span in line.get("spans", []))
            if y0 <= limit and text.strip():
                lines.append((round(y0), x0, text))
    return [text for _, _, text in sorted(lines)]


def process(upload, progress):
    """Devuelve pageCount, pages y proposedCuts; `progress(0..99)` informa el avance."""
    headerName = upload.sheetType.headerName
    document = open_pdf(original_path(upload))
    try:
        total = document.page_count
        detected = []
        for index in range(total):
            header = detect_header(top_lines(document.load_page(index)), headerName)
            header["index"] = index
            detected.append(header)
            progress(int(99 * (index + 1) / total))
    finally:
        document.close()
    pages = [UploadPage(index=h["index"], headerText=h["headerText"], number=h["number"],
                        isContinuation=h["isContinuation"], title=h["title"])
             for h in detected]
    cuts = [UploadCut(**cut) for cut in propose_cuts(detected)]
    return {"pageCount": total, "pages": pages, "proposedCuts": cuts}
