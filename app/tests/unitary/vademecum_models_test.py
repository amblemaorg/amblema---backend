# -*- coding: utf-8 -*-
# app/tests/unitary/vademecum_models_test.py

import unittest

from bson import ObjectId
from mongoengine import ValidationError


def _index_spec(model, fields):
    """Returns the index spec of `model` whose fields are exactly `fields`, or None."""
    for spec in model._meta["index_specs"]:
        if [f for f, _ in spec["fields"]] == fields:
            return spec
    return None


class VademecumCatalogModelsTest(unittest.TestCase):

    def _sheet_type(self, **kwargs):
        from app.models.vademecum import VademecumSheetType
        data = dict(name="Hora TAL", headerName="Hora TAL", codePrefix="HT",
                    color="#F2A93B", sort=1)
        data.update(kwargs)
        return VademecumSheetType(**data)

    def test_sheet_type_rejects_bad_color(self):
        with self.assertRaises(ValidationError):
            self._sheet_type(color="azul").validate()

    def test_area_defaults(self):
        from app.models.vademecum import VademecumArea
        area = VademecumArea(name="Geometría", sort=1)
        self.assertEqual(area.status, "1")
        self.assertIs(area.isDeleted, False)
        self.assertEqual(area.sheetTypes, [])

    def test_area_applies_to_its_sheet_types(self):
        from app.models.vademecum import VademecumArea
        hora = self._sheet_type(id=ObjectId())
        ingenio = self._sheet_type(id=ObjectId(), codePrefix="IM")
        area = VademecumArea(name="Lectura", sort=1, sheetTypes=[hora])
        self.assertTrue(area.applies_to(hora))
        self.assertTrue(area.applies_to(hora.id))
        self.assertFalse(area.applies_to(ingenio))

    def test_meta_collections_and_unique_partial_indexes(self):
        from app.models.vademecum import VademecumSheetType, VademecumArea
        self.assertEqual(VademecumSheetType._meta["collection"], "vademecum_sheet_types")
        self.assertEqual(VademecumArea._meta["collection"], "vademecum_areas")
        for model, field in ((VademecumSheetType, "codePrefix"), (VademecumArea, "name")):
            spec = _index_spec(model, [field])
            self.assertIsNotNone(spec, model.__name__)
            self.assertTrue(spec.get("unique"))
            self.assertEqual(spec.get("partialFilterExpression"), {"isDeleted": False})


class VademecumSheetModelsTest(unittest.TestCase):

    def _sheet(self, **kwargs):
        from app.models.vademecum import VademecumSheet, VademecumSheetType
        sheetType = VademecumSheetType(id=ObjectId(), name="Hora TAL", headerName="Hora TAL",
                                       codePrefix="HT", color="#F2A93B", sort=1)
        data = dict(sheetType=sheetType, number=41,
                    title="Identifica la palabra incongruente")
        data.update(kwargs)
        return VademecumSheet(**data)

    def test_build_sheet_code(self):
        from app.models.vademecum.sheet_model import build_sheet_code
        self.assertEqual(build_sheet_code("HT", 41), "HT-41")

    def test_clean_sets_code_from_type_prefix(self):
        sheet = self._sheet()
        sheet.clean()
        self.assertEqual(sheet.code, "HT-41")

    def test_models_have_no_series(self):
        from app.models.vademecum import VademecumSheet, VademecumSheetType
        from app.models.vademecum.download_model import DownloadSheet
        self.assertNotIn("series", VademecumSheetType._fields)
        self.assertNotIn("seriesId", VademecumSheet._fields)
        self.assertNotIn("seriesId", DownloadSheet._fields)

    def test_sheet_rejects_unknown_status_and_grade(self):
        with self.assertRaises(ValidationError):
            self._sheet(status="draft2").validate()
        with self.assertRaises(ValidationError):
            self._sheet(grades=["preschool"]).validate()
        self._sheet(grades=["3", "all"]).validate()

    def test_publish_errors_lists_missing_fields(self):
        from app.models.vademecum import SheetFile
        sheet = self._sheet(grades=[])
        self.assertEqual(set(sheet.publish_errors()), {"description", "grades", "file"})
        self.assertEqual(sheet.publish_errors()["grades"][0]["status"], "113")
        complete = self._sheet(description="Lectura", grades=["3"],
                               file=SheetFile(pdfPath="sheets/x/sheet.pdf", sizeBytes=10,
                                              pageCount=1))
        self.assertEqual(complete.publish_errors(), {})

    def test_sheet_defaults(self):
        sheet = self._sheet()
        self.assertEqual(sheet.status, "draft")
        self.assertEqual((sheet.downloadCount, sheet.ratingCount, sheet.ratingSum), (0, 0, 0))

    def test_sheet_indexes(self):
        from app.models.vademecum import VademecumSheet
        self.assertEqual(VademecumSheet._meta["collection"], "vademecum_sheets")
        for fields in (["sheetType", "number"], ["code"]):
            spec = _index_spec(VademecumSheet, fields)
            self.assertIsNotNone(spec, fields)
            self.assertTrue(spec.get("unique"))
            self.assertEqual(spec.get("partialFilterExpression"), {"isDeleted": False})
        text = _index_spec(VademecumSheet, ["title", "description", "searchText"])
        self.assertIsNotNone(text)
        self.assertEqual(text["default_language"], "spanish")
        self.assertEqual(text["weights"], {"title": 10, "description": 5, "searchText": 1})


class VademecumAccessModelsTest(unittest.TestCase):

    def test_account_email_is_normalized(self):
        from app.models.vademecum import VademecumTeacherAccount, VademecumAccessRequest
        account = VademecumTeacherAccount(email=" Maria.Perez@Gmail.com ", firstName="María",
                                          lastName="Pérez")
        account.clean()
        self.assertEqual(account.email, "maria.perez@gmail.com")
        request = VademecumAccessRequest(email=" Maria.Perez@Gmail.com ")
        request.clean()
        self.assertEqual(request.email, "maria.perez@gmail.com")

    def test_pending_account_validates_without_password(self):
        from app.models.vademecum import VademecumTeacherAccount
        account = VademecumTeacherAccount(email="a@b.co", firstName="A", lastName="B")
        account.validate()
        self.assertEqual(account.status, "pending")
        self.assertIs(account.password_is_valid("x"), False)

    def test_account_rejects_unknown_status(self):
        from app.models.vademecum import VademecumTeacherAccount
        with self.assertRaises(ValidationError):
            VademecumTeacherAccount(email="a@b.co", firstName="A", lastName="B",
                                    status="3").validate()

    def test_set_password_hashes_and_stamps(self):
        from app.models.vademecum import VademecumTeacherAccount
        account = VademecumTeacherAccount(email="a@b.co", firstName="A", lastName="B")
        account.set_password("12345678")
        self.assertNotEqual(account.password, "12345678")
        self.assertIs(account.password_is_valid("12345678"), True)
        self.assertIs(account.password_is_valid("87654321"), False)
        self.assertIsNotNone(account.passwordChangedAt)

    def test_hash_token_is_sha256(self):
        from app.models.vademecum.teacher_account_model import hash_token
        self.assertEqual(
            hash_token("abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_access_indexes(self):
        from app.models.vademecum import (
            VademecumTeacherAccount, VademecumAccessRequest, VademecumAuthorization)
        self.assertTrue(_index_spec(VademecumTeacherAccount, ["email"]).get("unique"))
        request = _index_spec(VademecumAccessRequest, ["email", "schoolYear"])
        self.assertTrue(request.get("unique"))
        self.assertEqual(request.get("partialFilterExpression"), {"status": "pending"})
        self.assertTrue(_index_spec(VademecumAuthorization, ["account", "schoolYear"]).get("unique"))


class VademecumActivityModelsTest(unittest.TestCase):

    def _rating(self, **kwargs):
        from app.models.vademecum import (
            VademecumRating, VademecumTeacherAccount, VademecumSheet)
        data = dict(account=VademecumTeacherAccount(id=ObjectId()),
                    sheet=VademecumSheet(id=ObjectId()), stars=4)
        data.update(kwargs)
        return VademecumRating(**data)

    def test_rating_stars_range(self):
        for stars in (0, 6):
            with self.assertRaises(ValidationError):
                self._rating(stars=stars).validate()
        self._rating(stars=5).validate()

    def test_set_comment_returns_to_pending_only_on_change(self):
        from datetime import datetime
        rating = self._rating(comment="Bien", commentStatus="approved",
                              moderatedAt=datetime.utcnow())
        rating.set_comment("Bien ")
        self.assertEqual(rating.commentStatus, "approved")
        self.assertIsNotNone(rating.moderatedAt)
        rating.set_comment("Muy bien")
        self.assertEqual(rating.comment, "Muy bien")
        self.assertEqual(rating.commentStatus, "pending")
        self.assertIsNone(rating.moderatedAt)
        rating.set_comment("")
        self.assertIsNone(rating.comment)
        self.assertIsNone(rating.commentStatus)

    def test_new_comment_starts_pending(self):
        rating = self._rating()
        rating.set_comment(" Útil para 3.º ")
        self.assertEqual(rating.comment, "Útil para 3.º")
        self.assertEqual(rating.commentStatus, "pending")

    def test_download_has_no_updated_at_and_validates_origin(self):
        from app.models.vademecum import (
            VademecumDownload, DownloadSheet, DownloadAccount, DownloadSchoolYear)
        self.assertNotIn("updatedAt", VademecumDownload._fields)
        download = VademecumDownload(
            sheet=DownloadSheet(id="s1", code="HT-41", title="T", sheetTypeId="t1",
                                sheetTypeName="Hora TAL"),
            account=DownloadAccount(id="a1", email="a@b.co", firstName="A", lastName="B"),
            schoolYear=DownloadSchoolYear(id="y1", name="2026-2027"),
            origin="school", isRedownload=False)
        with self.assertRaises(ValidationError):
            download.validate()
        download.origin = "external"
        download.validate()

    def test_activity_collections(self):
        from app.models.vademecum import (
            VademecumDownload, VademecumFavorite, VademecumRating, VademecumSiteContent,
            VademecumTeacherAccount, VademecumSheet)
        self.assertEqual(
            [m._meta["collection"] for m in (VademecumDownload, VademecumFavorite,
                                             VademecumRating, VademecumSiteContent)],
            ["vademecum_downloads", "vademecum_favorites", "vademecum_ratings",
             "vademecum_site_content"])
        self.assertTrue(_index_spec(VademecumFavorite, ["account", "sheet"]).get("unique"))
        self.assertTrue(_index_spec(VademecumRating, ["account", "sheet"]).get("unique"))
        self.assertTrue(_index_spec(VademecumSiteContent, ["key"]).get("unique"))
        self.assertIsNotNone(
            _index_spec(VademecumDownload, ["account.id", "schoolYear.id", "createdAt"]))
        fav = VademecumFavorite(account=VademecumTeacherAccount(id=ObjectId()),
                                sheet=VademecumSheet(id=ObjectId()))
        fav.clean()
        self.assertIsNotNone(fav.updatedAt)

    def test_auth_schema_and_html_sanitizer_edge_cases(self):
        from marshmallow import ValidationError as SchemaValidationError
        from app.schemas.vademecum.auth_schema import RegisterSchema
        from app.helpers.vademecum_html import sanitize_html
        with self.assertRaises(SchemaValidationError):
            RegisterSchema().load(["no-es-dict"])
        self.assertIsNone(sanitize_html(None))
        self.assertEqual(sanitize_html(u"<p/>Hola<br/></em><strong>abierto"),
                         u"<p></p>Hola<br><strong>abierto</strong>")


if __name__ == "__main__":
    unittest.main()
