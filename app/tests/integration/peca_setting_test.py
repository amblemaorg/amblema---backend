# app/tests/peca_setting_test.py


import unittest
import json
import io
from datetime import datetime

from app import create_app, db

from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import InitialWorshop, LapsePlanning


class PecaSettings(unittest.TestCase):
    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client

        self.schoolYear = SchoolYear(
            name="Test",
            startDate="2020-02-14",
            endDate="2020-09-14")
        self.schoolYear.save()

    def test_endpoint_initial_workshop(self):

        requestData = dict(
            agreementFile=(io.BytesIO(b'hi everyone'), 'agreementFile.pdf'),
            agreementDescription="Some description",
            planningMeetingFile=(io.BytesIO(b'hi everyone'),
                                 'planningMeetingFile.pdf'),
            planningMeetingDescription="Some description",
            teachersMeetingFile=(io.BytesIO(b'hi everyone'),
                                 'teachersMeetingFile.pdf'),
            teachersMeetingDescription="Some description"
        )
        res = self.client().post(
            '/pecasetting/initialworkshop',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        schoolYear = SchoolYear.objects.get(id=self.schoolYear.id)
        self.assertEqual(
            "agreementFile.pdf",
            schoolYear.pecaSetting.lapse1.initialWorkshop.agreementFile.name)

    def test_endpoint_lapse_planning(self):

        # lapse 1
        requestData = dict(
            proposalFundationFile=(io.BytesIO(
                b'hi everyone'), 'proposalFundationFile.pdf'),
            proposalFundationDescription="Some description",
            meetingDescription="Some description"
        )
        res = self.client().post(
            '/pecasetting/lapseplanning/1',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        schoolYear = SchoolYear.objects.get(id=self.schoolYear.id)
        self.assertEqual(
            "proposalFundationFile.pdf",
            schoolYear.pecaSetting.lapse1.lapsePlanning.proposalFundationFile.name)

        # lapse 2
        requestData = dict(
            proposalFundationFile=(io.BytesIO(
                b'hi everyone'), 'proposalFundationFile2.pdf'),
            proposalFundationDescription="Some description",
            meetingDescription="Some description"
        )
        res = self.client().post(
            '/pecasetting/lapseplanning/2',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        schoolYear = SchoolYear.objects.get(id=self.schoolYear.id)
        self.assertEqual(
            "proposalFundationFile2.pdf",
            schoolYear.pecaSetting.lapse2.lapsePlanning.proposalFundationFile.name)

        # lapse 3
        requestData = dict(
            proposalFundationFile=(io.BytesIO(
                b'hi everyone'), 'proposalFundationFile3.pdf'),
            proposalFundationDescription="Some description",
            meetingDescription="Some description"
        )
        res = self.client().post(
            '/pecasetting/lapseplanning/3',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        schoolYear = SchoolYear.objects.get(id=self.schoolYear.id)
        self.assertEqual(
            "proposalFundationFile3.pdf",
            schoolYear.pecaSetting.lapse3.lapsePlanning.proposalFundationFile.name)

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')
