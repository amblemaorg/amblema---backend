# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_compendium_samples_test.py
"""Detección sobre los compendios reales de muestra (API-09).

Los PDF (25–64 MB) no van al repo. Corre solo si VADEMECUM_SAMPLES_DIR apunta a la
carpeta con ellos (Vademecum/PDFs); si no, se omite.
"""

import os
import unittest
from unittest import mock

from flask import Flask

SAMPLES_DIR = os.getenv("VADEMECUM_SAMPLES_DIR")

try:
    import fitz  # noqa: F401  PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None

# archivo → (tipo, números esperados en orden, páginas por número con continuación)
EXPECTED = {
    "Troquel Ingenio 3er y 4to grado copia.pdf": (u"Ingenio Matemático", list(range(1, 11))),
    "Troquel Ingenio 5to y 6to grado copia.pdf": (u"Ingenio Matemático", list(range(1, 11))),
    "Troquel Momento X 3ER Y 4TO GRADO parte B copia.pdf": (u"Momento X", list(range(15, 32))),
    "Troquel Momento X 3ER Y 4TO GRADO.pdf": (u"Momento X", list(range(32, 42))),
    "lectura_troquel_ plantilla formato 5 copia.pdf": (u"Hora TAL", list(range(41, 50))),
    "lectura_troquel_ plantilla formato 6 copia.pdf": (u"Hora TAL", list(range(50, 58))),
}
# Ambiente aún no usa el encabezado común "Ambiente N. Título" (AMB-01): ninguna página
# debe inventar un número
AMBIENTE = "AMBIENTE 1ER LAPSO PARTE 1.pdf"


@unittest.skipUnless(SAMPLES_DIR and fitz, "VADEMECUM_SAMPLES_DIR sin definir o sin PyMuPDF")
class CompendiumSamplesTest(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["VADEMECUM_STORAGE_PATH"] = SAMPLES_DIR
        self.context = self.app.app_context()
        self.context.push()

    def tearDown(self):
        self.context.pop()

    def process(self, filename, headerName):
        from app.services.vademecum import compendium_processor
        upload = mock.Mock(originalPath=filename)
        upload.sheetType.headerName = headerName
        return compendium_processor.process(upload, lambda value: None)

    def test_numbered_compendiums(self):
        for filename, (headerName, numbers) in EXPECTED.items():
            result = self.process(filename, headerName)
            self.assertTrue(all(p.number for p in result["pages"]), filename)
            self.assertTrue(all(p.title for p in result["pages"]), filename)
            cuts = result["proposedCuts"]
            self.assertEqual([c.number for c in cuts], numbers, filename)
            covered = [i for c in cuts for i in c.pages]
            self.assertEqual(covered, list(range(result["pageCount"])), filename)
            # Toda página "A" quedó unida a la ficha de su número
            for page in result["pages"]:
                if page.isContinuation:
                    cut = next(c for c in cuts if page.index in c.pages)
                    self.assertEqual(cut.number, page.number)
                    self.assertGreater(len(cut.pages), 1)

    def test_ambiente_without_common_header_invents_nothing(self):
        result = self.process(AMBIENTE, u"Ambiente")
        self.assertEqual(result["pageCount"], 12)
        self.assertTrue(all(p.number is None for p in result["pages"]))
        self.assertEqual(len(result["proposedCuts"]), 12)
