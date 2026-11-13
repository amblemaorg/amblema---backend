# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_download_test.py
"""Descarga protegida y registro de la descarga (API-14)."""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime
from unittest import mock

from bson import ObjectId

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import create_school_year, enroll_vademecum_teacher

EMAIL = "maria.perez@gmail.com"
PDF_BYTES = b"%PDF-1.4 ficha de prueba"


class VademecumDownloadTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.context = self.app.app_context()
        self.context.push()
        from app import db
        self.db = db
        from app.helpers.vademecum_seeds import ensure_vademecum_indexes, seed_vademecum
        ensure_vademecum_indexes()
        seed_vademecum()
        self.client = self.app.test_client()
        self.storage = tempfile.mkdtemp()
        self.app.config["VADEMECUM_STORAGE_PATH"] = self.storage
        self.year = create_school_year(name="2026 - 2027", start=datetime(2026, 10, 14),
                                       end=datetime(2027, 8, 31))
        from app.models.vademecum import VademecumSheetType
        self.hora = VademecumSheetType.objects(codePrefix="HT").first()
        self.sheet = self.create_sheet(41, title=u"Identifica la palabra incongruente")
        self.account = self.create_account()
        from app.services.vademecum.token_service import issue_access_token
        self.token = issue_access_token(self.account)

    def tearDown(self):
        shutil.rmtree(self.storage, ignore_errors=True)
        drop_testing_database(self.db)
        self.context.pop()

    # --- Datos ---

    def create_account(self, email=EMAIL):
        from app.models.vademecum import VademecumTeacherAccount
        account = VademecumTeacherAccount(email=email, firstName=u"María", lastName=u"Pérez",
                                          status="1", emailVerifiedAt=datetime.utcnow())
        account.set_password("clave-segura")
        account.passwordChangedAt = datetime(2026, 1, 1)
        account.save()
        return account

    def create_sheet(self, number, status="published", withFile=True, **extra):
        from app.models.vademecum import SheetFile, VademecumSheet
        relative = "sheets/{}.pdf".format(number)
        if withFile:
            os.makedirs(os.path.join(self.storage, "sheets"), exist_ok=True)
            with open(os.path.join(self.storage, relative), "wb") as handle:
                handle.write(PDF_BYTES)
        data = dict(sheetType=self.hora, number=number, title=u"Ficha {}".format(number),
                    description=u"Descripción", grades=["3"], status=status,
                    publishedAt=datetime(2026, 11, 1),
                    file=SheetFile(pdfPath=relative, sizeBytes=len(PDF_BYTES), pageCount=1))
        data.update(extra)
        sheet = VademecumSheet(**data)
        sheet.save()
        return sheet

    def enroll(self, schoolName="Escuela Uno", grades=("3",)):
        return enroll_vademecum_teacher(self.year, EMAIL, grades=grades, schoolName=schoolName)

    def authorize(self):
        from app.models.vademecum import VademecumAuthorization
        VademecumAuthorization(account=self.account, schoolYear=self.year,
                               approvedBy=ObjectId()).save()

    def download(self, sheetId=None, data=None, token="default", **headers):
        if token == "default":
            token = self.token
        if token:
            headers["Authorization"] = "Bearer " + token
        return self.client.post(
            "/vademecum/sheets/{}/download".format(sheetId or self.sheet.id),
            headers=headers, data=json.dumps(data) if data is not None else None,
            content_type="application/json")

    def records(self):
        from app.models.vademecum import VademecumDownload
        return list(VademecumDownload.objects.order_by("createdAt"))

    def download_count(self):
        self.sheet.reload()
        return self.sheet.downloadCount

    def assert_error(self, res, httpStatus, field, code):
        self.assertEqual(res.status_code, httpStatus, res.get_data(as_text=True))
        self.assertEqual(res.get_json()[field][0]["status"], code)

    # --- Protección ---

    def test_download_requires_a_teacher_session(self):
        self.enroll()
        self.assertEqual(self.download(token=None).status_code, 401)
        self.assertEqual(self.download(token="no-es-un-token").status_code, 401)
        self.assertEqual(self.records(), [])

    def test_backoffice_token_cannot_download(self):
        from flask_jwt_extended import create_access_token
        self.enroll()
        self.assertEqual(self.download(token=create_access_token(identity="admin")).status_code,
                         401)

    def test_there_is_no_direct_url_to_the_pdf(self):
        self.enroll()
        get = self.client.get("/vademecum/sheets/{}/download".format(self.sheet.id),
                              headers={"Authorization": "Bearer " + self.token})
        self.assertEqual(get.status_code, 405)
        for path in ("/resources/files/sheets/41.pdf", "/sheets/41.pdf",
                     "/vademecum/sheets/41.pdf"):
            self.assertNotEqual(self.client.get(path).status_code, 200, path)
        detail = self.client.get("/vademecum/sheets/{}".format(self.sheet.id)).get_data(
            as_text=True)
        self.assertNotIn(".pdf", detail)

    # --- Matrícula ---

    def test_enrolled_teacher_downloads_the_pdf_and_it_is_recorded(self):
        from app.models.state_model import State
        from app.models.user_model import User
        schoolId = self.enroll()
        state = State(name="Lara")
        state.save()
        User._get_collection().update_one({"_id": ObjectId(schoolId)},
                                          {"$set": {"addressState": state.id}})

        res = self.download()
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        self.assertEqual(res.mimetype, "application/pdf")
        self.assertEqual(res.get_data(), PDF_BYTES)
        self.assertIn("attachment", res.headers["Content-Disposition"])
        self.assertIn("HT-41", res.headers["Content-Disposition"])
        self.assertEqual(res.headers["X-Vademecum-Redownload"], "false")
        self.assertIn("no-store", res.headers["Cache-Control"])

        [record] = self.records()
        self.assertEqual(res.headers["X-Vademecum-Download-Id"], str(record.id))
        self.assertEqual((record.sheet.id, record.sheet.code, record.sheet.title),
                         (str(self.sheet.id), "HT-41", u"Identifica la palabra incongruente"))
        self.assertEqual(record.sheet.sheetTypeId, str(self.hora.id))
        self.assertEqual((record.account.id, record.account.email),
                         (str(self.account.id), EMAIL))
        self.assertEqual((record.school.id, record.school.name, record.school.code),
                         (schoolId, "Escuela Uno", "OD1"))
        self.assertEqual((record.school.stateId, record.school.stateName),
                         (str(state.id), "Lara"))
        teacher = User._get_collection().find_one({"_id": ObjectId(schoolId)})["teachers"][0]
        self.assertEqual(record.teacherId, str(teacher["id"]))
        self.assertEqual((record.schoolYear.id, record.schoolYear.name),
                         (str(self.year.id), "2026 - 2027"))
        self.assertEqual((record.origin, record.isRedownload), ("enrollment", False))
        self.assertIsNotNone(record.createdAt)
        self.assertEqual(self.download_count(), 1)

    def test_downloading_again_in_the_same_year_is_a_redownload(self):
        self.enroll()
        self.assertEqual(self.download().headers["X-Vademecum-Redownload"], "false")
        again = self.download()
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again.headers["X-Vademecum-Redownload"], "true")
        self.assertEqual([r.isRedownload for r in self.records()], [False, True])
        self.assertEqual(self.download_count(), 1)

    def test_teacher_in_two_schools_chooses_the_attribution(self):
        first = self.enroll("Escuela Uno")
        second = self.enroll("Escuela Dos", grades=("5",))
        self.assert_error(self.download(), 400, "schoolId", "109")
        self.assert_error(self.download(data={"schoolId": str(ObjectId())}), 400,
                          "schoolId", "110")
        self.assertEqual(self.records(), [])

        res = self.download(data={"schoolId": second})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.records()[0].school.id, second)
        self.download(data={"schoolId": first})
        # Una sola descarga que cuenta por año, aunque cambie la escuela elegida
        self.assertEqual([r.school.id for r in self.records()], [second, first])
        self.assertEqual([r.isRedownload for r in self.records()], [False, True])

    def test_single_school_rejects_a_school_outside_the_enrollment(self):
        self.enroll()
        self.assert_error(self.download(data={"schoolId": str(ObjectId())}), 400,
                          "schoolId", "110")
        self.assert_error(self.download(data={"schoolId": 123}), 400, "schoolId", "110")

    # --- Autorización y sin acceso ---

    def test_authorized_external_teacher_downloads_without_school(self):
        self.authorize()
        res = self.download()
        self.assertEqual(res.status_code, 200)
        [record] = self.records()
        self.assertEqual((record.origin, record.school, record.teacherId),
                         ("external", None, None))
        self.assertEqual(self.download_count(), 1)

    def test_enrollment_has_priority_over_authorization(self):
        schoolId = self.enroll()
        self.authorize()
        self.download()
        self.assertEqual((self.records()[0].origin, self.records()[0].school.id),
                         ("enrollment", schoolId))

    def test_revoked_or_other_year_authorization_gives_no_access(self):
        from app.models.vademecum import VademecumAuthorization
        oldYear = create_school_year(name="2025 - 2026", status="2")
        VademecumAuthorization(account=self.account, schoolYear=oldYear,
                               approvedBy=ObjectId()).save()
        self.assert_error(self.download(), 403, "general", "108")
        VademecumAuthorization(account=self.account, schoolYear=self.year,
                               approvedBy=ObjectId(), revokedAt=datetime.utcnow()).save()
        self.assert_error(self.download(), 403, "general", "108")
        self.assertEqual(self.records(), [])

    def test_without_current_school_year_answers_117(self):
        self.enroll()
        self.year.status = "2"
        self.year.save()
        self.assert_error(self.download(), 409, "general", "117")

    # --- Ficha ---

    def test_only_published_sheets_with_a_file_are_delivered(self):
        self.enroll()
        draft = self.create_sheet(1, status="draft")
        unpublished = self.create_sheet(2, status="unpublished")
        deleted = self.create_sheet(3, isDeleted=True)
        missing = self.create_sheet(4, withFile=False)
        for sheetId in (draft.id, unpublished.id, deleted.id, missing.id, ObjectId(), "x"):
            self.assert_error(self.download(sheetId=sheetId), 404, "general", "5")
        self.assertEqual(self.records(), [])

    def test_pdf_path_outside_storage_is_never_served(self):
        from app.models.vademecum import SheetFile
        self.enroll()
        outside = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        outside.write(PDF_BYTES)
        outside.close()
        self.addCleanup(os.remove, outside.name)
        self.sheet.file = SheetFile(pdfPath=os.path.relpath(outside.name, self.storage))
        self.sheet.save()
        self.assert_error(self.download(), 404, "general", "5")

    def test_filename_keeps_accents_and_drops_unsafe_characters(self):
        self.enroll()
        sheet = self.create_sheet(7, title=u'Fracciones: "mitad" / cuarto en niño')
        disposition = self.download(sheetId=sheet.id).headers["Content-Disposition"]
        self.assertIn("filename*=UTF-8''HT-7%20Fracciones%20mitad%20cuarto%20en%20ni%C3%B1o.pdf",
                      disposition)

    def test_cors_exposes_the_download_headers(self):
        self.enroll()
        res = self.download(Origin="https://vademecum.amblema.org")
        exposed = res.headers.get("Access-Control-Expose-Headers", "").lower()
        self.assertIn("x-vademecum-download-id", exposed)
        self.assertIn("x-vademecum-redownload", exposed)

    # --- Concurrencia ---

    def test_simultaneous_first_downloads_count_once(self):
        """Si dos descargas pasan la consulta a la vez, el índice único deja contar solo una."""
        from app.models.vademecum import VademecumDownload
        self.enroll()
        self.download()
        realObjects = VademecumDownload.objects

        class StaleCheck(object):
            """La consulta de 'ya contada' no ve la descarga anterior."""
            def __call__(self, *args, **kwargs):
                if "__raw__" in kwargs:
                    return realObjects(id=ObjectId())
                return realObjects(*args, **kwargs)

        with mock.patch.object(VademecumDownload, "objects", StaleCheck()):
            res = self.download()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["X-Vademecum-Redownload"], "true")
        self.assertEqual([r.isRedownload for r in self.records()], [False, True])
        self.assertEqual(self.download_count(), 1)


if __name__ == "__main__":
    unittest.main()
