# -*- coding: utf-8 -*-
# app/tests/integration/yearbook_download_test.py

import json
import unittest
from datetime import datetime

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import (
    seed_base, create_location, create_coordinator, create_sponsor, create_school,
    create_school_year)
from app.helpers.handler_seeds import create_entities
from app.models.peca_project_model import PecaProject
from app.models.project_model import Project


class YearbookDownloadTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client

        create_entities()
        seed_base()
        self.state, self.municipality = create_location()
        self.schoolYear = create_school_year()
        self.coordinator = create_coordinator(self.state, self.municipality)
        self.sponsor = create_sponsor(self.state, self.municipality)
        self.school = create_school(self.state, self.municipality)

        self.project = Project(
            coordinator=self.coordinator, sponsor=self.sponsor, school=self.school)
        self.project.save()
        self.peca = self.newPeca(self.schoolYear)

    def tearDown(self):
        drop_testing_database(self.db)

    # ------------------------------------------------------------- helpers

    def newPeca(self, schoolYear):
        peca = PecaProject(
            schoolYear=schoolYear,
            schoolYearName=schoolYear.name,
            project={
                "id": str(self.project.id),
                "code": str(self.project.code),
                "coordinator": {"id": str(self.coordinator.id), "name": u"Ana Pérez"},
                "sponsor": {"id": str(self.sponsor.id), "name": self.sponsor.name},
                "school": {"id": str(self.school.id), "name": self.school.name,
                           "code": self.school.code},
            },
            school={"name": self.school.name, "code": self.school.code})
        peca.save()
        return peca

    def url(self, pecaId=None):
        return '/pecaprojects/{}/yearbook-download'.format(pecaId or self.peca.id)

    def get(self, url):
        return self.client().get(url)

    def patch(self, url, data):
        return self.client().patch(url, data=json.dumps(data),
                                   content_type='application/json')

    def flag(self, peca=None):
        return PecaProject.objects(id=(peca or self.peca).id).first().yearbookDownloadEnabled

    # --------------------------------------------------------------- tests

    def test_default_is_disabled(self):
        res = self.get(self.url())
        self.assertEqual(res.status_code, 200)
        body = json.loads(res.data)
        self.assertIs(body["yearbookDownloadEnabled"], False)
        self.assertIs(body["schoolYearActive"], True)
        self.assertEqual(body["pecaId"], str(self.peca.id))

    def test_patch_enables_and_disables(self):
        res = self.patch(self.url(), {"yearbookDownloadEnabled": True})
        self.assertEqual(res.status_code, 200)
        self.assertIs(json.loads(res.data)["yearbookDownloadEnabled"], True)
        self.assertIs(self.flag(), True)

        res = self.patch(self.url(), {"yearbookDownloadEnabled": False})
        self.assertEqual(res.status_code, 200)
        self.assertIs(json.loads(res.data)["yearbookDownloadEnabled"], False)
        self.assertIs(self.flag(), False)

    def test_patch_rejects_non_boolean(self):
        for body in ({}, {"yearbookDownloadEnabled": "true"}, {"yearbookDownloadEnabled": 1}):
            res = self.patch(self.url(), body)
            self.assertEqual(res.status_code, 400)
            self.assertIs(self.flag(), False)

    def test_patch_rejects_closed_school_year(self):
        closed = create_school_year(name="2024 - 2025", start=datetime(2024, 9, 1),
                                    end=datetime(2025, 7, 31), status="2")
        peca = self.newPeca(closed)
        res = self.patch(self.url(peca.id), {"yearbookDownloadEnabled": True})
        self.assertEqual(res.status_code, 400)
        self.assertIs(self.flag(peca), False)

        res = self.get(self.url(peca.id))
        self.assertEqual(res.status_code, 200)
        self.assertIs(json.loads(res.data)["schoolYearActive"], False)

    def test_unknown_peca_returns_404(self):
        for pecaId in ("5f0000000000000000000000", "abc"):
            self.assertEqual(self.get(self.url(pecaId)).status_code, 404)
            res = self.patch(self.url(pecaId), {"yearbookDownloadEnabled": True})
            self.assertEqual(res.status_code, 404)

    def test_list_only_active_year(self):
        closed = create_school_year(name="2024 - 2025", start=datetime(2024, 9, 1),
                                    end=datetime(2025, 7, 31), status="2")
        self.newPeca(closed)
        deleted = self.newPeca(self.schoolYear)
        deleted.isDeleted = True
        deleted.save()

        res = self.get('/pecaprojects/yearbook-download')
        self.assertEqual(res.status_code, 200)
        records = json.loads(res.data)["records"]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["projectId"], str(self.project.id))
        self.assertEqual(records[0]["pecaId"], str(self.peca.id))
        self.assertIs(records[0]["yearbookDownloadEnabled"], False)


if __name__ == '__main__':
    unittest.main()
