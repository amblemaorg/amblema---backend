# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_upload_test.py
"""Carga de compendios y su seguimiento desde el backoffice (API-07)."""

import io
import os
import shutil
import tempfile
import unittest
from datetime import datetime

from bson import ObjectId
from flask_jwt_extended import create_access_token

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import create_location

PDF = b"%PDF-1.7\n1 0 obj << >> endobj\ntrailer\n%%EOF\n"


class VademecumUploadBase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.context = self.app.app_context()
        self.context.push()
        from app import db
        self.db = db
        from app.helpers.handler_seeds import create_standard_roles
        from app.helpers.vademecum_seeds import ensure_vademecum_indexes, seed_vademecum
        create_standard_roles()
        ensure_vademecum_indexes()
        seed_vademecum()
        self.client = self.app.test_client()
        self.storage = tempfile.mkdtemp()
        self.app.config["VADEMECUM_STORAGE_PATH"] = self.storage
        from app.models.vademecum import VademecumSheetType
        self.hora = VademecumSheetType.objects(codePrefix="HT").first()
        self.ingenio = VademecumSheetType.objects(codePrefix="IM").first()
        self.state, self.municipality = create_location()
        self.admin = self.create_user("admin@test.com", "10000001", "admin")
        self.adminHeaders = self.headers(self.admin)

    def tearDown(self):
        shutil.rmtree(self.storage, ignore_errors=True)
        drop_testing_database(self.db)
        self.context.pop()

    def create_user(self, email, cardId, roleName):
        from app.models.admin_user_model import AdminUser
        from app.models.role_model import Role
        user = AdminUser(
            firstName="Admin", lastName="AmbLeMa", cardType="1", cardId=cardId,
            function="Admin", email=email, password="12345678", userType="1",
            phone="02322322323", role=Role.objects(devName=roleName).first(),
            addressState=self.state, addressMunicipality=self.municipality)
        user.setHashPassword()
        user.save()
        return user

    def headers(self, user):
        token = create_access_token({"id": str(user.id), "email": user.email})
        return {"Authorization": "Bearer " + token}

    def upload(self, content=PDF, filename="Troquel Hora TAL.pdf", headers=None, **form):
        form.setdefault("sheetTypeId", str(self.hora.id))
        data = dict(form)
        if content is not None:
            data["file"] = (io.BytesIO(content), filename)
        return self.client.post("/vademecum/admin/uploads", data=data,
                                content_type="multipart/form-data",
                                headers=self.adminHeaders if headers is None else headers)

    def assert_error(self, res, httpStatus, field, code):
        self.assertEqual(res.status_code, httpStatus, res.get_data(as_text=True))
        self.assertEqual(res.get_json()[field][0]["status"], code)


class VademecumUploadCreateTest(VademecumUploadBase):

    def test_admin_uploads_a_pdf_outside_public_paths(self):
        res = self.upload()
        self.assertEqual(res.status_code, 202, res.get_data(as_text=True))
        body = res.get_json()
        self.assertEqual((body["status"], body["progress"], body["errorMessage"]),
                         ("uploaded", 0, None))
        self.assertEqual(body["originalFileName"], "Troquel Hora TAL.pdf")
        self.assertEqual(body["originalSizeBytes"], len(PDF))
        self.assertEqual(body["sheetType"]["codePrefix"], "HT")
        self.assertIsNone(body["series"])
        self.assertEqual(body["createdBy"], {"id": str(self.admin.id), "name": "Admin AmbLeMa"})

        from app.models.vademecum import VademecumUpload
        upload = VademecumUpload.objects.get(id=body["id"])
        self.assertEqual(upload.originalPath, "uploads/{}/original.pdf".format(body["id"]))
        with open(os.path.join(self.storage, upload.originalPath), "rb") as handle:
            self.assertEqual(handle.read(), PDF)
        self.assertNotIn("resources", upload.originalPath)
        self.assertNotIn("originalPath", body)
        # Sin temporales sueltos
        self.assertEqual(sorted(os.listdir(os.path.join(self.storage, "uploads"))), [body["id"]])

    def test_series_is_required_and_must_belong_to_the_type(self):
        self.assert_error(self.upload(sheetTypeId=str(self.ingenio.id)), 400, "seriesId", "2")
        self.assert_error(self.upload(sheetTypeId=str(self.ingenio.id),
                                      seriesId=str(ObjectId())), 400, "seriesId", "1")
        res = self.upload(sheetTypeId=str(self.ingenio.id),
                          seriesId=str(self.ingenio.series[1].id))
        self.assertEqual(res.status_code, 202)
        self.assertEqual(res.get_json()["series"]["code"], "56")

    def test_sheet_type_is_required_and_must_exist(self):
        self.assert_error(self.upload(sheetTypeId=""), 400, "sheetTypeId", "2")
        self.assert_error(self.upload(sheetTypeId="x"), 400, "sheetTypeId", "1")
        self.hora.isDeleted = True
        self.hora.save()
        self.assert_error(self.upload(), 400, "sheetTypeId", "1")

    def test_only_pdf_files_are_accepted(self):
        self.assert_error(self.upload(content=None), 400, "file", "2")
        self.assert_error(self.upload(content=b"GIF89a no es un pdf", filename="x.pdf"),
                          400, "file", "115")
        self.assert_error(self.upload(content=b""), 400, "file", "115")
        # La extensión no importa: manda la firma del contenido
        self.assertEqual(self.upload(filename="compendio").status_code, 202)
        self.assertEqual(self.upload(content=b"\xef\xbb\xbf" + PDF).status_code, 202)

    def test_file_over_the_limit_is_rejected_and_not_kept(self):
        self.app.config["VADEMECUM_MAX_UPLOAD_MB"] = "1"
        big = PDF + b"0" * (1024 * 1024)
        self.assert_error(self.upload(content=big), 400, "file", "115")
        from app.models.vademecum import VademecumUpload
        self.assertEqual(VademecumUpload.objects.count(), 0)
        self.assertEqual(os.listdir(os.path.join(self.storage, "uploads")), [])

    def test_oversized_request_is_rejected_before_reading_the_body(self):
        self.app.config["VADEMECUM_MAX_UPLOAD_MB"] = "1"
        res = self.client.post("/vademecum/admin/uploads", data=b"x" * (2 * 1024 * 1024),
                               content_type="multipart/form-data; boundary=x",
                               headers=self.adminHeaders)
        self.assert_error(res, 400, "file", "115")

    def test_filename_cannot_escape_the_upload_folder(self):
        res = self.upload(filename="../../etc/passwd.pdf")
        self.assertEqual(res.get_json()["originalFileName"], "passwd.pdf")


class VademecumUploadPermissionTest(VademecumUploadBase):

    def test_requires_a_backoffice_admin(self):
        coordinator = self.create_user("coord@test.com", "10000002", "coordinator")
        for headers in ({}, self.headers(coordinator)):
            self.assertIn(self.upload(headers=headers).status_code, (401, 403))
            self.assertIn(self.client.get("/vademecum/admin/uploads",
                                          headers=headers).status_code, (401, 403))
        self.assertEqual(self.upload(headers=self.headers(coordinator)).status_code, 403)
        superadmin = self.create_user("super@test.com", "10000003", "superadmin")
        self.assertEqual(self.upload(headers=self.headers(superadmin)).status_code, 202)

    def test_teacher_token_is_rejected(self):
        from app.models.vademecum import VademecumTeacherAccount
        from app.services.vademecum.token_service import issue_access_token
        account = VademecumTeacherAccount(email="maria@test.com", firstName="M", lastName="P",
                                          status="1", emailVerifiedAt=datetime.utcnow())
        account.set_password("clave-segura")
        account.save()
        res = self.upload(headers={"Authorization": "Bearer " + issue_access_token(account)})
        self.assertIn(res.status_code, (401, 422))


class VademecumUploadTrackingTest(VademecumUploadBase):

    def test_list_is_paginated_newest_first_and_filters_by_status(self):
        from app.models.vademecum import VademecumUpload
        ids = [self.upload(filename="{}.pdf".format(i)).get_json()["id"] for i in range(3)]
        VademecumUpload.objects(id=ids[0]).update_one(set__status="error",
                                                      set__errorMessage="PDF dañado")
        res = self.client.get("/vademecum/admin/uploads?pageSize=2", headers=self.adminHeaders)
        body = res.get_json()
        self.assertEqual([r["id"] for r in body["records"]], [ids[2], ids[1]])
        self.assertEqual(body["pagination"], {"page": 1, "pageSize": 2, "total": 3, "pages": 2})
        self.assertNotIn("pages", body["records"][0])
        failed = self.client.get("/vademecum/admin/uploads?status=error",
                                 headers=self.adminHeaders).get_json()["records"]
        self.assertEqual([(r["id"], r["errorMessage"]) for r in failed],
                         [(ids[0], u"PDF dañado")])
        self.assert_error(self.client.get("/vademecum/admin/uploads?status=x",
                                          headers=self.adminHeaders), 400, "status", "1")

    def test_detail_shows_status_pages_and_cuts(self):
        from app.models.vademecum import UploadCut, UploadPage, VademecumUpload
        uploadId = self.upload().get_json()["id"]
        VademecumUpload.objects(id=uploadId).update_one(
            set__status="review", set__progress=100, set__pageCount=2,
            set__pages=[UploadPage(index=0, headerText=u"Hora TAL 1. Título", number=1,
                                   title=u"Título", thumbnailPath="uploads/x/pages/0.webp"),
                        UploadPage(index=1, headerText=u"Hora TAL 1A. Título", number=1,
                                   isContinuation=True, title=u"Título")],
            set__proposedCuts=[UploadCut(pages=[0, 1], number=1, title=u"Título")])
        body = self.client.get("/vademecum/admin/uploads/{}".format(uploadId),
                               headers=self.adminHeaders).get_json()
        self.assertEqual((body["status"], body["progress"], body["pageCount"]), ("review", 100, 2))
        self.assertEqual(body["pages"][0]["thumbnailUrl"],
                         "/vademecum/admin/uploads/{}/pages/0/thumbnail.webp".format(uploadId))
        self.assertIsNone(body["pages"][1]["thumbnailUrl"])
        self.assertTrue(body["pages"][1]["isContinuation"])
        self.assertEqual(body["proposedCuts"], [{"pages": [0, 1], "number": 1,
                                                 "title": u"Título", "excluded": False}])
        self.assertEqual((body["confirmedCuts"], body["sheets"]), ([], []))

    def test_unknown_upload_answers_404(self):
        for uploadId in (ObjectId(), "x"):
            self.assert_error(self.client.get("/vademecum/admin/uploads/{}".format(uploadId),
                                              headers=self.adminHeaders), 404, "general", "5")


class VademecumUploadDeleteTest(VademecumUploadBase):

    def create_sheet(self, upload, number, **extra):
        from app.models.vademecum import VademecumSheet
        sheet = VademecumSheet(sheetType=self.hora, number=number, title=u"Ficha",
                               upload=upload, **extra)
        sheet.save()
        upload.update(push__sheets=sheet)
        return sheet

    def delete(self, uploadId):
        return self.client.delete("/vademecum/admin/uploads/{}".format(uploadId),
                                  headers=self.adminHeaders)

    def test_delete_removes_files_and_draft_sheets(self):
        from app.models.vademecum import VademecumSheet, VademecumUpload
        uploadId = self.upload().get_json()["id"]
        upload = VademecumUpload.objects.get(id=uploadId)
        draft = self.create_sheet(upload, 1)
        res = self.delete(uploadId)
        self.assertEqual(res.status_code, 204)
        self.assertFalse(os.path.exists(os.path.join(self.storage, "uploads", uploadId)))
        self.assertTrue(VademecumUpload.objects.get(id=uploadId).isDeleted)
        self.assertTrue(VademecumSheet.objects.get(id=draft.id).isDeleted)
        self.assertEqual(self.delete(uploadId).status_code, 404)
        self.assertEqual(self.client.get("/vademecum/admin/uploads",
                                         headers=self.adminHeaders).get_json()["records"], [])

    def test_upload_with_sheets_ever_published_cannot_be_deleted(self):
        from app.models.vademecum import VademecumUpload
        uploadId = self.upload().get_json()["id"]
        upload = VademecumUpload.objects.get(id=uploadId)
        self.create_sheet(upload, 1, status="unpublished", publishedAt=datetime(2026, 11, 1))
        self.assert_error(self.delete(uploadId), 409, "general", "114")
        self.assertTrue(os.path.exists(os.path.join(self.storage, upload.originalPath)))

    def test_upload_being_processed_cannot_be_deleted(self):
        from app.models.vademecum import VademecumUpload
        uploadId = self.upload().get_json()["id"]
        VademecumUpload.objects(id=uploadId).update_one(set__status="processing")
        self.assert_error(self.delete(uploadId), 409, "general", "114")


if __name__ == "__main__":
    unittest.main()
