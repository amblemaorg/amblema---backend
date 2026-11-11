# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_processing_test.py
"""Procesamiento de compendios en segundo plano (API-08)."""

import threading
import time
import unittest
from datetime import datetime, timedelta
from unittest import mock

from app.tests.integration.vademecum_upload_test import VademecumUploadBase

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover - imagen sin PyMuPDF
    fitz = None

PROCESS = "app.services.vademecum.compendium_processor.process"


def make_pdf(pages=3):
    document = fitz.open()
    for index in range(pages):
        page = document.new_page()
        page.insert_text((72, 72), u"Hora TAL {}. Página de prueba".format(index + 1))
    data = document.tobytes()
    document.close()
    return data


def make_compendium(headers):
    """PDF con el tipo en una línea y "<N>[A]. <Título>" en la siguiente (como las muestras)."""
    document = fitz.open()
    for header in headers:
        page = document.new_page()
        page.insert_text((72, 60), u"Hora TAL")
        page.insert_text((72, 80), header)
        page.insert_text((72, 400), u"Cuerpo de la ficha")
    data = document.tobytes()
    document.close()
    return data


@unittest.skipUnless(fitz, "PyMuPDF no está instalado")
class VademecumProcessingTest(VademecumUploadBase):

    def setUp(self):
        super(VademecumProcessingTest, self).setUp()
        self.app.config["VADEMECUM_PROCESSING_MODE"] = "inline"

    def upload_doc(self, uploadId):
        from app.models.vademecum import VademecumUpload
        return VademecumUpload.objects.get(id=uploadId)

    def detail(self, uploadId):
        return self.client.get("/vademecum/admin/uploads/{}".format(uploadId),
                               headers=self.adminHeaders).get_json()

    def reprocess(self, uploadId):
        return self.client.post("/vademecum/admin/uploads/{}/reprocess".format(uploadId),
                                headers=self.adminHeaders)

    # --- Resultado ---

    def test_valid_pdf_ends_in_review_with_its_pages(self):
        res = self.upload(content=make_pdf(3))
        self.assertEqual(res.status_code, 202)
        body = self.detail(res.get_json()["id"])
        self.assertEqual((body["status"], body["progress"], body["pageCount"]), ("review", 100, 3))
        self.assertEqual([p["index"] for p in body["pages"]], [0, 1, 2])
        self.assertIsNotNone(body["processedAt"])
        upload = self.upload_doc(body["id"])
        self.assertIsNone(upload.processingId)

    def test_headers_are_detected_and_cuts_proposed(self):
        pdf = make_compendium([u"41. Identifica la Palabra", u"41A. Identifica la Palabra",
                               u"42.Entrevistas", u"Sin encabezado"])
        body = self.detail(self.upload(content=pdf).get_json()["id"])
        self.assertEqual([(p["number"], p["isContinuation"]) for p in body["pages"]],
                         [(41, False), (41, True), (42, False), (None, False)])
        self.assertEqual(body["pages"][1]["headerText"], u"Hora TAL 41A. Identifica la Palabra")
        self.assertEqual([(c["pages"], c["number"], c["title"]) for c in body["proposedCuts"]],
                         [([0, 1], 41, u"Identifica la Palabra"), ([2], 42, u"Entrevistas"),
                          ([3], None, None)])

    def test_damaged_pdf_ends_in_error_with_a_clear_message(self):
        res = self.upload(content=b"%PDF-1.4 esto no es un pdf de verdad")
        body = self.detail(res.get_json()["id"])
        self.assertEqual(body["status"], "error")
        self.assertIn(u"dañado", body["errorMessage"])

    def test_unexpected_failure_is_visible_without_internal_details(self):
        with mock.patch(PROCESS, side_effect=RuntimeError("/srv/secret/path explotó")):
            uploadId = self.upload(content=make_pdf(1)).get_json()["id"]
        body = self.detail(uploadId)
        self.assertEqual((body["status"], body["errorMessage"]),
                         ("error", u"No se pudo procesar el PDF."))

    # --- Sin bloquear ---

    def test_request_answers_before_processing_ends(self):
        self.app.config["VADEMECUM_PROCESSING_MODE"] = "thread"
        started, release = threading.Event(), threading.Event()

        def slow(upload, progress):
            started.set()
            progress(50)
            release.wait(10)
            return {"pageCount": 1, "pages": [], "proposedCuts": []}

        with mock.patch(PROCESS, side_effect=slow):
            res = self.upload(content=make_pdf(1))
            self.assertEqual(res.status_code, 202)
            uploadId = res.get_json()["id"]
            self.assertTrue(started.wait(5))
            body = self.detail(uploadId)
            self.assertEqual((body["status"], body["progress"]), ("processing", 50))
            release.set()
            self.wait_for(uploadId, "review")

    def wait_for(self, uploadId, status, seconds=10):
        deadline = time.time() + seconds
        while time.time() < deadline:
            if self.upload_doc(uploadId).status == status:
                return
            time.sleep(0.05)
        self.fail("upload did not reach {}".format(status))

    # --- Varios workers ---

    def test_only_one_worker_claims_an_upload(self):
        from app.services.vademecum import processing_service
        self.app.config["VADEMECUM_PROCESSING_MODE"] = "off"
        uploadId = self.upload(content=make_pdf(1)).get_json()["id"]
        first, firstId = processing_service.claim(uploadId)
        second, secondId = processing_service.claim(uploadId)
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(self.upload_doc(uploadId).processingId, firstId)

    def test_run_on_an_already_claimed_upload_does_nothing(self):
        from app.services.vademecum import processing_service
        self.app.config["VADEMECUM_PROCESSING_MODE"] = "off"
        uploadId = self.upload(content=make_pdf(1)).get_json()["id"]
        processing_service.claim(uploadId)
        with mock.patch(PROCESS) as process:
            processing_service.run(self.app, self.upload_doc(uploadId).id)
        process.assert_not_called()

    # --- Interrumpido y reintento ---

    def make_stale(self, uploadId, status="processing"):
        from app.models.vademecum import VademecumUpload
        VademecumUpload.objects(id=uploadId).update_one(
            set__status=status, set__processingId="worker-muerto", set__progress=40,
            set__heartbeatAt=datetime.utcnow() - timedelta(minutes=10))

    def test_interrupted_processing_is_marked_and_can_be_retried(self):
        self.app.config["VADEMECUM_PROCESSING_MODE"] = "off"
        uploadId = self.upload(content=make_pdf(2)).get_json()["id"]
        self.make_stale(uploadId)
        body = self.detail(uploadId)
        self.assertEqual(body["status"], "error")
        self.assertIn("interrumpi", body["errorMessage"])

        self.app.config["VADEMECUM_PROCESSING_MODE"] = "inline"
        res = self.reprocess(uploadId)
        self.assertEqual(res.status_code, 202)
        self.assertEqual(self.detail(uploadId)["status"], "review")

    def test_upload_never_picked_up_is_marked_interrupted(self):
        self.app.config["VADEMECUM_PROCESSING_MODE"] = "off"
        uploadId = self.upload(content=make_pdf(1)).get_json()["id"]
        self.make_stale(uploadId, status="uploaded")
        self.assertEqual(self.detail(uploadId)["status"], "error")

    def test_fresh_processing_cannot_be_reprocessed(self):
        from app.models.vademecum import VademecumUpload
        self.app.config["VADEMECUM_PROCESSING_MODE"] = "off"
        uploadId = self.upload(content=make_pdf(1)).get_json()["id"]
        VademecumUpload.objects(id=uploadId).update_one(set__status="processing",
                                                        set__heartbeatAt=datetime.utcnow())
        self.assert_error(self.reprocess(uploadId), 409, "general", "114")
        VademecumUpload.objects(id=uploadId).update_one(set__status="done")
        self.assert_error(self.reprocess(uploadId), 409, "general", "114")

    def test_reprocess_discards_cuts_not_generated(self):
        from app.models.vademecum import UploadCut, VademecumUpload
        uploadId = self.upload(content=make_pdf(2)).get_json()["id"]
        VademecumUpload.objects(id=uploadId).update_one(
            set__confirmedCuts=[UploadCut(pages=[0, 1], number=1)])
        self.assertEqual(self.reprocess(uploadId).status_code, 202)
        self.assertEqual(self.detail(uploadId)["confirmedCuts"], [])

    def test_worker_that_lost_the_upload_stops_writing(self):
        from app.services.vademecum import processing_service
        self.app.config["VADEMECUM_PROCESSING_MODE"] = "off"
        uploadId = self.upload(content=make_pdf(1)).get_json()["id"]
        upload, processingId = processing_service.claim(uploadId)
        # Otro proceso la marcó interrumpida y la reintentó
        self.make_stale(uploadId)
        processing_service.mark_stale()
        with self.assertRaises(processing_service.LostClaim):
            processing_service.report_progress(upload, processingId, 80)
        self.assertFalse(processing_service.finish(
            upload, processingId, {"pageCount": 1, "pages": [], "proposedCuts": []}))
        self.assertEqual(self.upload_doc(uploadId).status, "error")


if __name__ == "__main__":
    unittest.main()
