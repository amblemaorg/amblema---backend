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

    def test_series_rejects_unknown_grade(self):
        from app.models.vademecum import SheetSeries
        sheetType = self._sheet_type(
            series=[SheetSeries(name="7", code="7", grades=["7"], sort=1)])
        with self.assertRaises(ValidationError):
            sheetType.validate()

    def test_get_series_returns_match_or_none(self):
        from app.models.vademecum import SheetSeries
        series = [SheetSeries(name="3.º y 4.º grado", code="34", grades=["3", "4"], sort=1),
                  SheetSeries(name="5.º y 6.º grado", code="56", grades=["5", "6"], sort=2)]
        sheetType = self._sheet_type(series=series)
        self.assertIs(sheetType.get_series(series[1].id), series[1])
        self.assertIs(sheetType.get_series(str(series[1].id)), series[1])
        self.assertIsNone(sheetType.get_series(ObjectId()))
        self.assertIsNone(sheetType.get_series(None))

    def test_series_codes_must_be_unique_within_type(self):
        from app.models.vademecum import SheetSeries
        sheetType = self._sheet_type(series=[
            SheetSeries(name="A", code="34", grades=["3", "4"], sort=1),
            SheetSeries(name="B", code="34", grades=["3", "4"], sort=2)])
        with self.assertRaises(ValidationError):
            sheetType.validate()
        sheetType.series[1].isDeleted = True
        sheetType.validate()

    def test_area_defaults(self):
        from app.models.vademecum import VademecumArea
        area = VademecumArea(name="Geometría", sort=1)
        self.assertEqual(area.status, "1")
        self.assertIs(area.isDeleted, False)

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
        self.assertEqual(build_sheet_code("HT", None, 41), "HT-41")
        self.assertEqual(build_sheet_code("IM", "34", 1), "IM34-1")

    def test_clean_sets_code_from_type_and_series(self):
        from app.models.vademecum import SheetSeries, VademecumSheetType
        series = SheetSeries(name="3.º y 4.º grado", code="34", grades=["3", "4"], sort=1)
        sheetType = VademecumSheetType(id=ObjectId(), name="Ingenio Matemático",
                                       headerName="Ingenio Matemático", codePrefix="IM",
                                       color="#2F80ED", sort=2, series=[series])
        sheet = self._sheet(sheetType=sheetType, seriesId=series.id, number=1)
        sheet.clean()
        self.assertEqual(sheet.code, "IM34-1")
        plain = self._sheet()
        plain.clean()
        self.assertEqual(plain.code, "HT-41")

    def _ingenio(self):
        from app.models.vademecum import SheetSeries, VademecumSheetType
        series = SheetSeries(name="3.º y 4.º grado", code="34", grades=["3", "4"], sort=1)
        return VademecumSheetType(id=ObjectId(), name="Ingenio Matemático",
                                  headerName="Ingenio Matemático", codePrefix="IM",
                                  color="#2F80ED", sort=2, series=[series])

    def test_sheet_rejects_series_from_another_type(self):
        with self.assertRaises(ValidationError):
            self._sheet(sheetType=self._ingenio(), seriesId=ObjectId(), number=1).validate()

    def test_sheet_requires_series_when_type_has_series(self):
        with self.assertRaises(ValidationError):
            self._sheet(sheetType=self._ingenio(), number=1).validate()

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
        for fields in (["sheetType", "seriesId", "number"], ["code"]):
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
            VademecumDownload, VademecumFavorite, VademecumRating, VademecumSiteContent)
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


if __name__ == "__main__":
    unittest.main()
