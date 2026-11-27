# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_priority_test.py
"""Catálogo priorizado por grado (CON-03) y portada con lanzamientos y destacadas (CON-05)."""

import unittest
from datetime import datetime, timedelta

from bson import ObjectId

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import create_school_year, enroll_vademecum_teacher

EMAIL = "maria.perez@gmail.com"


class VademecumPriorityTest(unittest.TestCase):

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
        self.base = datetime(2026, 11, 1)
        self.account = self.create_account(EMAIL)
        from app.services.vademecum.token_service import issue_access_token
        self.token = issue_access_token(self.account)

    def tearDown(self):
        drop_testing_database(self.db)
        self.context.pop()

    # --- Datos ---

    def create_account(self, email):
        from app.models.vademecum import VademecumTeacherAccount
        account = VademecumTeacherAccount(email=email, firstName=u"María", lastName=u"Pérez",
                                          status="1", emailVerifiedAt=datetime.utcnow())
        account.set_password("clave-segura")
        account.passwordChangedAt = datetime(2026, 1, 1)
        account.save()
        return account

    def sheet(self, number, grades, days, status="published", **extra):
        from app.models.vademecum import VademecumSheet
        sheet = VademecumSheet(sheetType=self.hora, number=number, title=u"Ficha {}".format(number),
                               grades=grades, status=status,
                               publishedAt=self.base + timedelta(days=days), **extra)
        sheet.save()
        return sheet

    def seed_catalog(self):
        """Seis fichas; la más nueva primero: HT-1 (5.º), HT-2 (3.º), HT-3 (todos), ..."""
        self.sheet(1, ["5"], 5)
        self.sheet(2, ["3"], 4)
        self.sheet(3, ["all"], 3)
        self.sheet(4, ["6"], 2)
        self.sheet(5, ["4"], 1)
        self.sheet(6, ["3", "5"], 0)

    def auth(self, token=None):
        return {"Authorization": "Bearer " + (token or self.token)}

    def codes(self, path, headers=None, **params):
        res = self.client.get(path, headers=headers or {}, query_string=params)
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        return [r["code"] for r in res.get_json()["records"]]

    NEWEST = ["HT-1", "HT-2", "HT-3", "HT-4", "HT-5", "HT-6"]

    # --- CON-03: catálogo priorizado ---

    def test_visitor_keeps_the_plain_order(self):
        self.seed_catalog()
        enroll_vademecum_teacher(self.year, EMAIL, grades=("3", "4"))
        self.assertEqual(self.codes("/vademecum/sheets"), self.NEWEST)

    def test_enrolled_teacher_sees_their_grades_first_without_hiding_the_rest(self):
        self.seed_catalog()
        enroll_vademecum_teacher(self.year, EMAIL, grades=("3", "4"))
        res = self.client.get("/vademecum/sheets", headers=self.auth())
        # Grados 3, 4 y "Todos" primero (más nuevas antes); luego el resto con el mismo orden
        self.assertEqual([r["code"] for r in res.get_json()["records"]],
                         ["HT-2", "HT-3", "HT-5", "HT-6", "HT-1", "HT-4"])
        self.assertEqual(res.get_json()["pagination"]["total"], 6)

    def test_pagination_crosses_from_the_priority_group_to_the_rest(self):
        self.seed_catalog()
        enroll_vademecum_teacher(self.year, EMAIL, grades=("3", "4"))
        self.assertEqual(self.codes("/vademecum/sheets", self.auth(), pageSize=3),
                         ["HT-2", "HT-3", "HT-5"])
        res = self.client.get("/vademecum/sheets?pageSize=3&page=2", headers=self.auth())
        self.assertEqual([r["code"] for r in res.get_json()["records"]], ["HT-6", "HT-1", "HT-4"])
        self.assertEqual(res.get_json()["pagination"],
                         {"page": 2, "pageSize": 3, "total": 6, "pages": 2})
        self.assertEqual(self.codes("/vademecum/sheets", self.auth(), pageSize=4, page=2),
                         ["HT-1", "HT-4"])

    def test_the_requested_order_applies_inside_each_group(self):
        self.seed_catalog()
        from app.models.vademecum import VademecumSheet
        for number, count in ((4, 9), (1, 5), (5, 3), (2, 1)):
            VademecumSheet.objects(number=number).update(set__downloadCount=count)
        enroll_vademecum_teacher(self.year, EMAIL, grades=("3", "4"))
        self.assertEqual(self.codes("/vademecum/sheets", self.auth(), sort="popular"),
                         ["HT-5", "HT-2", "HT-3", "HT-6", "HT-4", "HT-1"])

    def test_rating_sort_keeps_the_enrolled_grade_first(self):
        # HT-2 (grado 3) está peor valorada que HT-1 (grado 5): gana la prioridad CON-03
        self.seed_catalog()
        from app.models.vademecum import VademecumSheet
        VademecumSheet.objects(number=2).update(set__ratingSum=4, set__ratingCount=1)
        VademecumSheet.objects(number=1).update(set__ratingSum=10, set__ratingCount=2)
        enroll_vademecum_teacher(self.year, EMAIL, grades=("3", "4"))
        self.assertEqual(self.codes("/vademecum/sheets", self.auth(), sort="rating"),
                         ["HT-2", "HT-3", "HT-5", "HT-6", "HT-1", "HT-4"])

    def test_an_explicit_grade_filter_wins_over_the_priority(self):
        self.seed_catalog()
        enroll_vademecum_teacher(self.year, EMAIL, grades=("3", "4"))
        self.assertEqual(self.codes("/vademecum/sheets", self.auth(), grade="5"),
                         ["HT-1", "HT-3", "HT-6"])

    def test_a_text_search_is_not_reordered(self):
        self.seed_catalog()
        enroll_vademecum_teacher(self.year, EMAIL, grades=("3", "4"))
        self.assertEqual(self.codes("/vademecum/sheets", self.auth(), q="HT-4"), ["HT-4"])
        self.assertEqual(self.codes("/vademecum/sheets", self.auth(), q="HT", sort="relevance"),
                         self.codes("/vademecum/sheets", q="HT", sort="relevance"))

    def test_teachers_without_enrollment_or_with_a_bad_token_get_the_plain_order(self):
        self.seed_catalog()
        self.assertEqual(self.codes("/vademecum/sheets", self.auth()), self.NEWEST)
        enroll_vademecum_teacher(self.year, EMAIL, grades=("3", "4"))
        self.assertEqual(self.codes("/vademecum/sheets", self.auth("no-es-un-token")), self.NEWEST)

    def test_enrollment_without_sections_has_no_grades_to_prioritize(self):
        self.seed_catalog()
        enroll_vademecum_teacher(self.year, EMAIL, grades=())
        self.assertEqual(self.codes("/vademecum/sheets", self.auth()), self.NEWEST)

    # --- CON-05: lanzamientos y destacadas ---

    def get_home(self, headers=None):
        res = self.client.get("/vademecum/home", headers=headers or {})
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        return res.get_json()

    def test_home_is_public_and_featured_is_empty_without_downloads(self):
        self.seed_catalog()
        body = self.get_home()
        self.assertEqual([r["code"] for r in body["newReleases"]], self.NEWEST)
        self.assertEqual(body["featured"], [])
        self.assertEqual(body["newReleases"][0]["sheetType"]["codePrefix"], "HT")

    def test_new_releases_are_the_eight_most_recent_published_sheets(self):
        for number in range(1, 11):
            self.sheet(number, ["3"], number)
        self.sheet(11, ["3"], 20, status="draft")
        self.sheet(12, ["3"], 21, status="unpublished")
        codes = [r["code"] for r in self.get_home()["newReleases"]]
        self.assertEqual(codes, ["HT-{}".format(n) for n in range(10, 2, -1)])

    def test_featured_are_the_eight_most_downloaded_and_skip_sheets_without_downloads(self):
        for number in range(1, 11):
            self.sheet(number, ["3"], number, downloadCount=number if number > 1 else 0)
        self.sheet(11, ["3"], 11, status="unpublished", downloadCount=99)
        codes = [r["code"] for r in self.get_home()["featured"]]
        self.assertEqual(codes, ["HT-{}".format(n) for n in range(10, 2, -1)])
        self.assertNotIn("HT-1", codes)

    def test_home_comments_skips_unpublished_sheets(self):
        from app.models.vademecum import VademecumRating
        for number in range(1, 6):
            sheet = self.sheet(number, ["3"], number, ratingCount=1, ratingSum=5)
            rating = VademecumRating(account=self.account, sheet=sheet, stars=5,
                                     comment=u"Comentario {}".format(number),
                                     commentStatus="approved").save()
            VademecumRating.objects(id=rating.id).update(
                set__updatedAt=self.base + timedelta(days=number))
        for number in range(6, 15):
            sheet = self.sheet(number, ["3"], number, status="unpublished")
            rating = VademecumRating(account=self.account, sheet=sheet, stars=4,
                                     comment=u"Comentario oculto {}".format(number),
                                     commentStatus="approved").save()
            VademecumRating.objects(id=rating.id).update(
                set__updatedAt=self.base + timedelta(days=100 + number))
        body = self.get_home()
        # Los 9 comentarios más recientes son de fichas despublicadas: /home debe devolver 3
        # comentarios de fichas publicadas igualmente, no 0.
        self.assertEqual(len(body["comments"]), 3)
        self.assertEqual([c["sheet"]["code"] for c in body["comments"]], ["HT-5", "HT-4", "HT-3"])
        self.assertEqual(body["ratingSummary"]["count"], 5)

    def test_home_puts_the_teachers_grades_first_in_both_lists(self):
        self.seed_catalog()
        from app.models.vademecum import VademecumSheet
        for number, count in ((1, 8), (2, 1), (4, 9), (5, 3)):
            VademecumSheet.objects(number=number).update(set__downloadCount=count)
        enroll_vademecum_teacher(self.year, EMAIL, grades=("3", "4"))
        body = self.get_home(self.auth())
        self.assertEqual([r["code"] for r in body["newReleases"]],
                         ["HT-2", "HT-3", "HT-5", "HT-6", "HT-1", "HT-4"])
        # Con descargas: HT-5 (3) y HT-2 (1) de sus grados antes que HT-4 (9) y HT-1 (8)
        self.assertEqual([r["code"] for r in body["featured"]], ["HT-5", "HT-2", "HT-4", "HT-1"])
        self.assertEqual([r["code"] for r in self.get_home()["featured"]],
                         ["HT-4", "HT-1", "HT-5", "HT-2"])


if __name__ == "__main__":
    unittest.main()
