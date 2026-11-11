# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_generation_test.py
"""Cortes confirmados y generación de fichas en borrador (API-11)."""

import os
import unittest
from datetime import datetime, timedelta
from unittest import mock

from app.tests.integration.vademecum_processing_test import fitz, make_compendium
from app.tests.integration.vademecum_upload_test import VademecumUploadBase

HEADERS = [u"41. Identifica la Palabra", u"41A. Identifica la Palabra", u"42.Entrevistas",
           u"Sin encabezado", u"43. Rimas"]


def cut(pages, number=None, title=None, excluded=False):
    return {"pages": pages, "number": number, "title": title, "excluded": excluded}


@unittest.skipUnless(fitz, "PyMuPDF no está instalado")
class VademecumGenerationBase(VademecumUploadBase):

    def setUp(self):
        super(VademecumGenerationBase, self).setUp()
        self.app.config["VADEMECUM_PROCESSING_MODE"] = "inline"

    def new_upload(self, headers=HEADERS, **form):
        res = self.upload(content=make_compendium(headers), **form)
        self.assertEqual(res.status_code, 202)
        return res.get_json()["id"]

    def put_cuts(self, uploadId, cuts):
        return self.client.put("/vademecum/admin/uploads/{}/cuts".format(uploadId),
                               json={"cuts": cuts}, headers=self.adminHeaders)

    def generate(self, uploadId, headers=None):
        return self.client.post("/vademecum/admin/uploads/{}/generate".format(uploadId),
                                headers=self.adminHeaders if headers is None else headers)

    def detail(self, uploadId):
        return self.client.get("/vademecum/admin/uploads/{}".format(uploadId),
                               headers=self.adminHeaders).get_json()

    def upload_doc(self, uploadId):
        from app.models.vademecum import VademecumUpload
        return VademecumUpload.objects.get(id=uploadId)


class VademecumCutsTest(VademecumGenerationBase):

    def assert_cuts_error(self, res):
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json()["cuts"][0]["status"], "116")

    def test_proposed_cuts_can_be_confirmed_as_they_are(self):
        uploadId = self.new_upload()
        proposed = self.detail(uploadId)["proposedCuts"]
        # La página sin encabezado no es ficha: se excluye
        proposed[2]["excluded"] = True
        res = self.put_cuts(uploadId, proposed)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["confirmedCuts"], [
            cut([0, 1], 41, u"Identifica la Palabra"), cut([2], 42, u"Entrevistas"),
            cut([3], excluded=True), cut([4], 43, u"Rimas")])

    def test_join_keeps_number_and_title_of_first_page(self):
        uploadId = self.new_upload()
        res = self.put_cuts(uploadId, [cut([0, 1, 2]), cut([3], excluded=True), cut([4])])
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["confirmedCuts"][0],
                         cut([0, 1, 2], 41, u"Identifica la Palabra"))

    def test_split_and_edited_values(self):
        uploadId = self.new_upload()
        res = self.put_cuts(uploadId, [
            cut([0], 41), cut([1], 44, u"Segunda parte"), cut([2]),
            cut([3], 45, u"  Página sin encabezado  "), cut([4])])
        self.assertEqual(res.status_code, 200)
        self.assertEqual([(c["number"], c["title"]) for c in res.get_json()["confirmedCuts"]], [
            (41, u"Identifica la Palabra"), (44, u"Segunda parte"), (42, u"Entrevistas"),
            (45, u"Página sin encabezado"), (43, u"Rimas")])

    def test_remove_pages_with_excluded_cut(self):
        uploadId = self.new_upload()
        res = self.put_cuts(uploadId, [cut([0, 1]), cut([2, 3], excluded=True), cut([4])])
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["confirmedCuts"][1],
                         cut([2, 3], excluded=True))

    def test_invalid_cuts(self):
        uploadId = self.new_upload()
        invalid = {
            "empty": [],
            "no pages": [cut([]), cut([0, 1, 2, 3, 4])],
            "not consecutive": [cut([0, 2]), cut([1], excluded=True), cut([3, 4])],
            "overlap": [cut([0, 1]), cut([1, 2]), cut([3], excluded=True), cut([4])],
            "missing page": [cut([0, 1]), cut([2]), cut([4])],
            "missing last": [cut([0, 1]), cut([2]), cut([3], excluded=True)],
            "out of range": [cut([0, 1]), cut([2]), cut([3], excluded=True), cut([4, 5])],
            "unordered": [cut([2]), cut([0, 1]), cut([3], excluded=True), cut([4])],
            "no number": [cut([0, 1]), cut([2]), cut([3]), cut([4])],
            "repeated": [cut([0]), cut([1]), cut([2]), cut([3], excluded=True), cut([4])],
        }
        for name, cuts in invalid.items():
            with self.subTest(name):
                self.assert_cuts_error(self.put_cuts(uploadId, cuts))
        self.assertEqual(self.upload_doc(uploadId).confirmedCuts, [])

    def test_payload_validation(self):
        uploadId = self.new_upload()
        self.assertEqual(self.put_cuts(uploadId, [cut([-1])]).status_code, 400)
        res = self.client.put("/vademecum/admin/uploads/{}/cuts".format(uploadId),
                              json={}, headers=self.adminHeaders)
        self.assertEqual(res.status_code, 400)
        self.assertIn("cuts", res.get_json())

    def test_only_in_review(self):
        self.app.config["VADEMECUM_PROCESSING_MODE"] = "off"
        uploadId = self.new_upload()  # queda en `uploaded`
        res = self.put_cuts(uploadId, [cut([0])])
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.get_json()["general"][0]["status"], "114")

    def test_requires_admin_and_existing_upload(self):
        uploadId = self.new_upload()
        coordinator = self.create_user("coord@test.com", "10000002", "coordinator")
        res = self.client.put("/vademecum/admin/uploads/{}/cuts".format(uploadId),
                              json={"cuts": []}, headers=self.headers(coordinator))
        self.assertEqual(res.status_code, 403)
        self.assertEqual(self.put_cuts("5f0000000000000000000000", [cut([0])]).status_code, 404)


class VademecumGenerateTest(VademecumGenerationBase):

    def confirmed_upload(self, **form):
        uploadId = self.new_upload(**form)
        res = self.put_cuts(uploadId, [cut([0, 1]), cut([2]), cut([3], excluded=True),
                                       cut([4])])
        self.assertEqual(res.status_code, 200)
        return uploadId

    def sheets(self):
        from app.models.vademecum import VademecumSheet
        return list(VademecumSheet.objects(isDeleted=False).order_by("number"))

    def test_generates_one_draft_per_cut(self):
        uploadId = self.confirmed_upload()
        res = self.generate(uploadId)
        self.assertEqual(res.status_code, 202)

        body = self.detail(uploadId)
        self.assertEqual((body["status"], body["progress"], body["errorMessage"]),
                         ("done", 100, None))
        sheets = self.sheets()
        self.assertEqual([(s.code, s.title, s.status, s.sourcePages) for s in sheets], [
            ("HT-41", u"Identifica la Palabra", "draft", [0, 1]),
            ("HT-42", u"Entrevistas", "draft", [2]),
            ("HT-43", u"Rimas", "draft", [4])])
        self.assertEqual([s["code"] for s in body["sheets"]], ["HT-41", "HT-42", "HT-43"])
        self.assertEqual(body["sheetCount"], 3)
        first = sheets[0]
        self.assertEqual(first.file.pageCount, 2)
        self.assertEqual(str(first.upload.id), uploadId)
        self.assertIn(u"41A. Identifica la Palabra", first.searchText)
        self.assertNotIn(u"Entrevistas", first.searchText)
        for path in (first.file.pdfPath, first.file.thumbnailPath, first.file.previewPath):
            self.assertTrue(os.path.isfile(os.path.join(self.storage, path)), path)
        self.assertIsNone(self.upload_doc(uploadId).processingId)

    def test_series_gives_code_and_grades(self):
        series = self.ingenio.active_series()[0]
        uploadId = self.new_upload(
            headers=[u"1. Conteo", u"2. Valor posicional"], sheetTypeId=str(self.ingenio.id),
            seriesId=str(series.id))
        # El encabezado del compendio dice "Hora TAL"; los números se ponen a mano
        self.assertEqual(self.put_cuts(uploadId, [cut([0], 1, u"Conteo"),
                                                  cut([1], 2, u"Valor")]).status_code, 200)
        self.generate(uploadId)
        sheets = self.sheets()
        self.assertEqual([s.code for s in sheets],
                         ["IM{}-1".format(series.code), "IM{}-2".format(series.code)])
        self.assertEqual(sheets[0].grades, list(series.grades))

    def test_existing_sheets_are_reported_and_not_duplicated(self):
        from app.models.vademecum import VademecumSheet
        VademecumSheet(sheetType=self.hora, number=42, title=u"Ya cargada").save()
        uploadId = self.confirmed_upload()
        self.generate(uploadId)
        body = self.detail(uploadId)
        self.assertEqual(body["status"], "done")
        self.assertEqual(body["errorMessage"],
                         u"Fichas que ya existían y no se generaron: HT-42.")
        self.assertEqual([s.title for s in self.sheets()],
                         [u"Identifica la Palabra", u"Ya cargada", u"Rimas"])
        self.assertEqual([s["code"] for s in body["sheets"]], ["HT-41", "HT-43"])

    def test_requires_confirmed_cuts_and_review(self):
        uploadId = self.new_upload()
        res = self.generate(uploadId)  # sin cortes confirmados
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.get_json()["general"][0]["status"], "114")
        # Solo excluidos tampoco
        self.put_cuts(uploadId, [cut([0, 1, 2, 3, 4], excluded=True)])
        self.assertEqual(self.generate(uploadId).status_code, 409)

    def test_cannot_generate_twice_nor_change_cuts_after(self):
        uploadId = self.confirmed_upload()
        self.generate(uploadId)
        self.assertEqual(self.generate(uploadId).status_code, 409)
        self.assertEqual(self.put_cuts(uploadId, [cut([0, 1, 2, 3, 4])]).status_code, 409)
        self.assertEqual(len(self.sheets()), 3)

    def test_background_mode_answers_generating(self):
        uploadId = self.confirmed_upload()
        self.app.config["VADEMECUM_PROCESSING_MODE"] = "off"
        res = self.generate(uploadId)
        self.assertEqual(res.status_code, 202)
        self.assertEqual(res.get_json()["status"], "generating")
        self.assertEqual(self.put_cuts(uploadId, [cut([0, 1, 2, 3, 4])]).status_code, 409)

    def test_failure_marks_error_and_retry_skips_created_sheets(self):
        uploadId = self.confirmed_upload()
        from app.services.vademecum import sheet_media
        real = sheet_media.build_sheet_files
        calls = []

        def flaky(source, sheetId, pages=None):
            calls.append(pages)
            if len(calls) == 2:
                raise RuntimeError("/srv/ruta/secreta falló")
            return real(source, sheetId, pages=pages)

        with mock.patch.object(sheet_media, "build_sheet_files", side_effect=flaky):
            self.generate(uploadId)
        body = self.detail(uploadId)
        self.assertEqual(body["status"], "error")
        self.assertEqual(body["errorMessage"], u"No se pudieron generar las fichas.")
        # La ficha que falló no queda a medias; la primera sí quedó
        self.assertEqual([s.code for s in self.sheets()], ["HT-41"])

        self.assertEqual(self.generate(uploadId).status_code, 202)
        body = self.detail(uploadId)
        self.assertEqual(body["status"], "done")
        self.assertEqual(body["errorMessage"],
                         u"Fichas que ya existían y no se generaron: HT-41.")
        self.assertEqual([s.code for s in self.sheets()], ["HT-41", "HT-42", "HT-43"])
        self.assertEqual(body["sheetCount"], 3)

    def test_interrupted_generation_is_marked_stale(self):
        uploadId = self.confirmed_upload()
        self.app.config["VADEMECUM_PROCESSING_MODE"] = "off"
        self.generate(uploadId)
        from app.models.vademecum import VademecumUpload
        VademecumUpload.objects(id=uploadId).update_one(
            set__heartbeatAt=datetime.utcnow() - timedelta(minutes=10))
        body = self.detail(uploadId)
        self.assertEqual(body["status"], "error")
        self.app.config["VADEMECUM_PROCESSING_MODE"] = "inline"
        self.assertEqual(self.generate(uploadId).status_code, 202)
        self.assertEqual(self.detail(uploadId)["status"], "done")

    def test_lost_claim_stops_writing(self):
        uploadId = self.confirmed_upload()
        from app.models.vademecum import VademecumUpload
        from app.services.vademecum import generation_service

        processingId = generation_service.claim_generation(self.upload_doc(uploadId))
        VademecumUpload.objects(id=uploadId).update_one(set__processingId="otro")
        generation_service.run(self.app, self.upload_doc(uploadId).id, processingId)
        self.assertEqual(self.sheets(), [])
        self.assertEqual(self.upload_doc(uploadId).status, "generating")
