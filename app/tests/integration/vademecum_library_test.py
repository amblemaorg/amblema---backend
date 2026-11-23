# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_library_test.py
"""Favoritos, mis descargas y textos públicos del sitio (API-15)."""

import unittest
from datetime import datetime

from bson import ObjectId

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import create_school_year


class VademecumLibraryTest(unittest.TestCase):

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
        self.year = create_school_year(name="2026 - 2027", start=datetime(2026, 10, 14),
                                       end=datetime(2027, 8, 31))
        from app.models.vademecum import VademecumSheetType
        self.hora = VademecumSheetType.objects(codePrefix="HT").first()
        self.maria = self.create_account("maria@test.com", u"María")
        self.jose = self.create_account("jose@test.com", u"José")
        from app.services.vademecum.token_service import issue_access_token
        self.mariaHeaders = {"Authorization": "Bearer " + issue_access_token(self.maria)}
        self.joseHeaders = {"Authorization": "Bearer " + issue_access_token(self.jose)}

    def tearDown(self):
        drop_testing_database(self.db)
        self.context.pop()

    # --- Datos ---

    def create_account(self, email, firstName):
        from app.models.vademecum import VademecumTeacherAccount
        account = VademecumTeacherAccount(email=email, firstName=firstName, lastName=u"Prueba",
                                          status="1", emailVerifiedAt=datetime.utcnow())
        account.set_password("clave-segura")
        account.passwordChangedAt = datetime(2026, 1, 1)
        account.save()
        return account

    def create_sheet(self, number, status="published"):
        from app.models.vademecum import VademecumSheet
        sheet = VademecumSheet(sheetType=self.hora, number=number, title=u"Ficha {}".format(number),
                               description=u"Descripción", grades=["3"], status=status,
                               publishedAt=datetime(2026, 11, 1))
        sheet.save()
        return sheet

    def add_download(self, account, sheet, when, redownload=False, year=None, school="default",
                     origin="enrollment"):
        from app.models.vademecum import VademecumDownload
        year = year or self.year
        if school == "default":
            school = {"id": "5f1a2b3c4d5e6f7081920a01", "name": u"Escuela Uno", "code": "OD1"}
        VademecumDownload(
            sheet={"id": str(sheet.id), "code": sheet.code, "title": sheet.title},
            account={"id": str(account.id), "email": account.email},
            schoolYear={"id": str(year.id), "name": year.name},
            school=school, origin=origin, isRedownload=redownload, createdAt=when).save()

    def favorites(self, headers, query=""):
        return self.client.get("/vademecum/me/favorites" + query, headers=headers)

    def downloads(self, headers, query=""):
        return self.client.get("/vademecum/me/downloads" + query, headers=headers)

    def put_favorite(self, sheetId, headers=None):
        return self.client.put("/vademecum/me/favorites/{}".format(sheetId),
                               headers=headers or self.mariaHeaders)

    def delete_favorite(self, sheetId, headers=None):
        return self.client.delete("/vademecum/me/favorites/{}".format(sheetId),
                                  headers=headers or self.mariaHeaders)

    # --- Textos del sitio ---

    def test_site_content_is_public_and_lists_every_section(self):
        res = self.client.get("/vademecum/site-content")
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        self.assertEqual([r["key"] for r in res.get_json()["records"]],
                         ["about", "access_request", "home"])

    # --- Favoritos ---

    def test_everything_requires_a_teacher_token(self):
        sheet = self.create_sheet(41)
        self.assertEqual(self.client.get("/vademecum/me/favorites").status_code, 401)
        self.assertEqual(self.client.put("/vademecum/me/favorites/{}".format(sheet.id)).status_code, 401)
        self.assertEqual(self.client.delete("/vademecum/me/favorites/{}".format(sheet.id)).status_code, 401)
        self.assertEqual(self.client.get("/vademecum/me/downloads").status_code, 401)

    def test_adding_a_favorite_twice_keeps_one_and_lists_the_newest_first(self):
        first, second = self.create_sheet(41), self.create_sheet(42)
        self.assertEqual(self.put_favorite(first.id).status_code, 204)
        self.assertEqual(self.put_favorite(first.id).status_code, 204)
        self.assertEqual(self.put_favorite(second.id).status_code, 204)
        body = self.favorites(self.mariaHeaders).get_json()
        self.assertEqual([r["sheet"]["id"] for r in body["records"]], [str(second.id), str(first.id)])
        self.assertEqual(body["pagination"]["total"], 2)
        self.assertEqual(body["records"][0]["sheet"]["title"], u"Ficha 42")
        self.assertIn("createdAt", body["records"][0])

    def test_favorites_are_private_to_each_teacher(self):
        sheet = self.create_sheet(41)
        self.put_favorite(sheet.id)
        self.assertEqual(self.favorites(self.joseHeaders).get_json()["pagination"]["total"], 0)
        # Quitar el favorito de otro no borra el de María
        self.assertEqual(self.delete_favorite(sheet.id, self.joseHeaders).status_code, 204)
        self.assertEqual(self.favorites(self.mariaHeaders).get_json()["pagination"]["total"], 1)

    def test_only_published_sheets_can_be_favorited(self):
        draft = self.create_sheet(43, status="draft")
        self.assertEqual(self.put_favorite(draft.id).status_code, 404)
        self.assertEqual(self.put_favorite(ObjectId()).status_code, 404)
        self.assertEqual(self.put_favorite("no-es-un-id").status_code, 404)
        self.assertEqual(self.favorites(self.mariaHeaders).get_json()["pagination"]["total"], 0)

    def test_unpublished_sheet_leaves_the_list_but_keeps_the_favorite(self):
        keep, hidden = self.create_sheet(41), self.create_sheet(42)
        self.put_favorite(keep.id)
        self.put_favorite(hidden.id)
        hidden.status = "unpublished"
        hidden.save()
        body = self.favorites(self.mariaHeaders).get_json()
        self.assertEqual([r["sheet"]["id"] for r in body["records"]], [str(keep.id)])
        self.assertEqual(body["pagination"]["total"], 1)
        hidden.status = "published"
        hidden.save()
        self.assertEqual(self.favorites(self.mariaHeaders).get_json()["pagination"]["total"], 2)

    def test_removing_a_favorite_is_idempotent(self):
        from unittest import mock
        from mongoengine import NotUniqueError
        from app.models.vademecum import VademecumFavorite
        sheet = self.create_sheet(41)
        self.put_favorite(sheet.id)
        with mock.patch.object(VademecumFavorite, "objects", side_effect=NotUniqueError("dup")):
            self.assertEqual(self.put_favorite(sheet.id).status_code, 204)
        self.assertEqual(self.delete_favorite(sheet.id).status_code, 204)
        self.assertEqual(self.delete_favorite(sheet.id).status_code, 204)
        self.assertEqual(self.favorites(self.mariaHeaders).get_json()["pagination"]["total"], 0)
        self.assertEqual(self.delete_favorite("no-es-un-id").status_code, 404)

    def test_favorites_are_paginated_and_validate_the_page(self):
        for number in (41, 42, 43):
            self.put_favorite(self.create_sheet(number).id)
        body = self.favorites(self.mariaHeaders, "?pageSize=2&page=2").get_json()
        self.assertEqual(len(body["records"]), 1)
        self.assertEqual(body["pagination"], {"page": 2, "pageSize": 2, "total": 3, "pages": 2})
        self.assertEqual(self.favorites(self.mariaHeaders, "?pageSize=0").status_code, 400)
        self.assertEqual(self.favorites(self.mariaHeaders, "?page=x").status_code, 400)

    # --- Mis descargas ---

    def test_downloads_default_to_the_current_year_one_row_per_sheet(self):
        sheet, other = self.create_sheet(41), self.create_sheet(42)
        self.add_download(self.maria, sheet, datetime(2026, 11, 1))
        self.add_download(self.maria, sheet, datetime(2026, 11, 5), redownload=True)
        self.add_download(self.maria, other, datetime(2026, 11, 3))
        res = self.downloads(self.mariaHeaders)
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        body = res.get_json()
        self.assertEqual([r["sheet"]["id"] for r in body["records"]], [str(sheet.id), str(other.id)])
        first = body["records"][0]
        self.assertEqual((first["timesDownloaded"], first["origin"]), (2, "enrollment"))
        self.assertEqual(first["lastDownloadedAt"], "2026-11-05T00:00:00Z")
        self.assertEqual(first["school"], {"id": "5f1a2b3c4d5e6f7081920a01",
                                           "name": u"Escuela Uno", "code": "OD1"})
        self.assertEqual(first["schoolYear"], {"id": str(self.year.id), "name": "2026 - 2027"})
        self.assertEqual(body["years"], [{"id": str(self.year.id), "name": "2026 - 2027"}])
        self.assertEqual(body["pagination"]["total"], 2)

    def test_downloads_of_other_teachers_are_not_visible(self):
        sheet = self.create_sheet(41)
        self.add_download(self.maria, sheet, datetime(2026, 11, 1))
        body = self.downloads(self.joseHeaders).get_json()
        self.assertEqual((body["records"], body["years"], body["pagination"]["total"]), ([], [], 0))

    def test_downloads_can_be_filtered_by_year(self):
        previous = create_school_year(name="2025 - 2026", start=datetime(2025, 10, 1),
                                      end=datetime(2026, 7, 31), status="2")
        old, new = self.create_sheet(41), self.create_sheet(42)
        self.add_download(self.maria, old, datetime(2026, 3, 1), year=previous)
        self.add_download(self.maria, new, datetime(2026, 11, 1))
        current = self.downloads(self.mariaHeaders).get_json()
        self.assertEqual([r["sheet"]["id"] for r in current["records"]], [str(new.id)])
        self.assertEqual({y["name"] for y in current["years"]}, {"2025 - 2026", "2026 - 2027"})
        past = self.downloads(self.mariaHeaders, "?schoolYearId={}".format(previous.id)).get_json()
        self.assertEqual([r["sheet"]["id"] for r in past["records"]], [str(old.id)])
        empty = self.downloads(self.mariaHeaders, "?schoolYearId={}".format(ObjectId())).get_json()
        self.assertEqual(empty["pagination"]["total"], 0)
        self.assertEqual(self.downloads(self.mariaHeaders, "?schoolYearId=xx").status_code, 400)

    def test_external_download_has_no_school_and_a_nameless_school_does_not_break_the_list(self):
        external, nameless = self.create_sheet(41), self.create_sheet(42)
        self.add_download(self.maria, external, datetime(2026, 11, 1), school=None, origin="external")
        self.add_download(self.maria, nameless, datetime(2026, 11, 2),
                          school={"id": "5f1a2b3c4d5e6f7081920a02"})
        rows = {r["sheet"]["id"]: r for r in self.downloads(self.mariaHeaders).get_json()["records"]}
        self.assertEqual((rows[str(external.id)]["school"], rows[str(external.id)]["origin"]),
                         (None, "external"))
        self.assertEqual(rows[str(nameless.id)]["school"],
                         {"id": "5f1a2b3c4d5e6f7081920a02", "name": None, "code": None})

    def test_unpublished_sheets_are_left_out_of_the_download_list(self):
        sheet = self.create_sheet(41)
        self.add_download(self.maria, sheet, datetime(2026, 11, 1))
        sheet.status = "unpublished"
        sheet.save()
        body = self.downloads(self.mariaHeaders).get_json()
        self.assertEqual((body["records"], body["pagination"]["total"]), ([], 0))
        self.assertEqual(len(body["years"]), 1)

    def test_downloads_are_paginated_and_validate_the_page(self):
        for number in (41, 42, 43):
            self.add_download(self.maria, self.create_sheet(number), datetime(2026, 11, number - 40))
        body = self.downloads(self.mariaHeaders, "?pageSize=2").get_json()
        self.assertEqual(len(body["records"]), 2)
        self.assertEqual(body["pagination"]["pages"], 2)
        self.assertEqual(self.downloads(self.mariaHeaders, "?pageSize=101").status_code, 400)


if __name__ == "__main__":
    unittest.main()
