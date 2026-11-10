# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_seeds_test.py

import unittest

from mongoengine import NotUniqueError

from app import create_app
from app.tests.base import drop_testing_database


class VademecumSeedsTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.context = self.app.app_context()
        self.context.push()
        from app import db
        self.db = db
        from app.helpers.vademecum_seeds import ensure_vademecum_indexes
        ensure_vademecum_indexes()

    def tearDown(self):
        drop_testing_database(self.db)
        self.context.pop()

    def _sheet_type(self, codePrefix="HT"):
        from app.models.vademecum import VademecumSheetType
        return VademecumSheetType.objects(codePrefix=codePrefix).first()

    def test_ensure_indexes_covers_all_models(self):
        from app.helpers.vademecum_seeds import ensure_vademecum_indexes
        from app.models.vademecum import VADEMECUM_MODELS
        self.assertEqual(len(VADEMECUM_MODELS), 11)
        self.assertEqual(ensure_vademecum_indexes(), 11)

    def test_seed_creates_catalog_once(self):
        from app.helpers.vademecum_seeds import seed_vademecum
        from app.models.vademecum import VademecumSheetType
        self.assertEqual(seed_vademecum(), {"sheetTypes": 4, "areas": 4, "siteContent": 3})
        self.assertEqual(seed_vademecum(), {"sheetTypes": 0, "areas": 0, "siteContent": 0})
        self.assertEqual(VademecumSheetType.objects.count(), 4)
        ingenio = self._sheet_type("IM")
        self.assertEqual([s.code for s in ingenio.series], ["34", "56"])
        self.assertEqual(ingenio.series[0].grades, ["3", "4"])

    def test_seed_does_not_overwrite_admin_edits(self):
        from app.helpers.vademecum_seeds import seed_vademecum
        seed_vademecum()
        hora = self._sheet_type("HT")
        hora.color = "#000000"
        hora.save()
        seed_vademecum()
        self.assertEqual(self._sheet_type("HT").color, "#000000")

    def test_seed_does_not_revive_deleted_type_or_renamed_area(self):
        from app.helpers.vademecum_seeds import seed_vademecum
        from app.models.vademecum import VademecumSheetType, VademecumArea
        seed_vademecum()
        momento = self._sheet_type("MX")
        momento.isDeleted = True
        momento.save()
        area = VademecumArea.objects(name=u"Geometría").first()
        area.name = u"Geometría y medida"
        area.save()
        self.assertEqual(seed_vademecum(), {"sheetTypes": 0, "areas": 0, "siteContent": 0})
        self.assertEqual(VademecumSheetType.objects(codePrefix="MX", isDeleted=False).count(), 0)
        self.assertEqual(VademecumArea.objects(name=u"Geometría").count(), 0)

    def _save_sheet(self, sheetType, number, seriesId=None, **kwargs):
        from app.models.vademecum import VademecumSheet
        sheet = VademecumSheet(sheetType=sheetType, seriesId=seriesId, number=number,
                               title=kwargs.pop("title", "Ficha"), **kwargs)
        sheet.save()
        return sheet

    def test_unique_sheet_without_series(self):
        from app.helpers.vademecum_seeds import seed_vademecum
        seed_vademecum()
        hora = self._sheet_type("HT")
        first = self._save_sheet(hora, 41)
        with self.assertRaises(NotUniqueError):
            self._save_sheet(hora, 41)
        first.isDeleted = True
        first.save()
        second = self._save_sheet(hora, 41)
        self.assertEqual(second.code, "HT-41")

    def test_same_number_in_different_series_is_allowed(self):
        from app.helpers.vademecum_seeds import seed_vademecum
        seed_vademecum()
        ingenio = self._sheet_type("IM")
        a = self._save_sheet(ingenio, 1, seriesId=ingenio.series[0].id)
        b = self._save_sheet(ingenio, 1, seriesId=ingenio.series[1].id)
        self.assertEqual((a.code, b.code), ("IM34-1", "IM56-1"))

    def test_spanish_text_search_ignores_accents(self):
        from app.helpers.vademecum_seeds import seed_vademecum
        from app.models.vademecum import VademecumSheet
        seed_vademecum()
        self._save_sheet(self._sheet_type("HT"), 1, title=u"Problemas de conteo geométrico",
                         status="published")
        self.assertEqual(VademecumSheet.objects.search_text("geometrico").count(), 1)

    def test_email_unique_across_formats(self):
        from app.models.vademecum import VademecumTeacherAccount
        VademecumTeacherAccount(email="maria@x.co", firstName="M", lastName="P").save()
        with self.assertRaises(NotUniqueError):
            VademecumTeacherAccount(email=" MARIA@x.co ", firstName="M", lastName="P").save()


if __name__ == "__main__":
    unittest.main()
