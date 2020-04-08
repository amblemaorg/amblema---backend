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
        # lapse 1
        res = self.client().post(
            '/pecasetting/initialworkshop/1',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        schoolYear = SchoolYear.objects.get(id=self.schoolYear.id)
        self.assertEqual(
            "agreementFile.pdf",
            schoolYear.pecaSetting.lapse1.initialWorkshop.agreementFile.name)

        # lapse 2
        requestData = dict(
            agreementFile=(io.BytesIO(b'hi everyone'), 'agreementFile2.pdf'),
            agreementDescription="Some description",
            planningMeetingFile=(io.BytesIO(b'hi everyone'),
                                 'planningMeetingFile2.pdf'),
            planningMeetingDescription="Some description",
            teachersMeetingFile=(io.BytesIO(b'hi everyone'),
                                 'teachersMeetingFile.pdf'),
            teachersMeetingDescription="Some description"
        )
        res = self.client().post(
            '/pecasetting/initialworkshop/2',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        schoolYear = SchoolYear.objects.get(id=self.schoolYear.id)
        self.assertEqual(
            "agreementFile2.pdf",
            schoolYear.pecaSetting.lapse2.initialWorkshop.agreementFile.name)

        # lapse 3
        requestData = dict(
            agreementFile=(io.BytesIO(b'hi everyone'), 'agreementFile3.pdf'),
            agreementDescription="Some description",
            planningMeetingFile=(io.BytesIO(b'hi everyone'),
                                 'planningMeetingFile3.pdf'),
            planningMeetingDescription="Some description",
            teachersMeetingFile=(io.BytesIO(b'hi everyone'),
                                 'teachersMeetingFile3.pdf'),
            teachersMeetingDescription="Some description"
        )
        res = self.client().post(
            '/pecasetting/initialworkshop/3',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        res = self.client().get(
            '/pecasetting/initialworkshop/3')
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(
            "agreementFile3.pdf",
            result['agreementFile']['name'])

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

        schoolYear = SchoolYear.objects.get(id=self.schoolYear.pk)
        self.assertEqual(
            "proposalFundationFile3.pdf",
            schoolYear.pecaSetting.lapse3.lapsePlanning.proposalFundationFile.name)

    def test_endpoint_amblecoins(self):

        # lapse1
        requestData = dict(
            teachersMeetingFile=(io.BytesIO(b'hi everyone'),
                                 'teachersMeetingFile.pdf'),
            teachersMeetingDescription="Some description",
            piggyBankDescription="Some description",
            piggyBankSlider=json.dumps(
                [{"image": "http://localhost:10505/resources/images/learningmodules/5e4edc7edb90150c560b2dc1.png",
                  "description": "some description"}]
            )
        )
        res = self.client().post(
            '/pecasetting/amblecoins/1',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        schoolYear = SchoolYear.objects.get(id=self.schoolYear.pk)
        self.assertEqual(
            "teachersMeetingFile.pdf",
            schoolYear.pecaSetting.lapse1.ambleCoins.teachersMeetingFile.name)

        res = self.client().get(
            '/pecasetting/amblecoins/1')
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual('some description',
                         result['piggyBankSlider'][0]['description'])

        # lapse 2
        requestData = dict(
            teachersMeetingFile=(io.BytesIO(b'hi everyone'),
                                 'teachersMeetingFile.pdf'),
            teachersMeetingDescription="Some description",
            piggyBankDescription="Some description",
            piggyBankSlider=json.dumps(
                [
                    {
                        "image": "http://localhost:10505/resources/images/learningmodules/5e4edc7edb90150c560b2dc1.png",
                        "description": "some description"
                    },
                    {
                        "image": "http://localhost:10505/resources/images/learningmodules/5e4edc7edb90150c560b2dc1.png",
                        "description": "some description2"
                    }
                ]
            )
        )
        res = self.client().post(
            '/pecasetting/amblecoins/2',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        schoolYear = SchoolYear.objects.get(id=self.schoolYear.pk)
        self.assertEqual(
            "some description2",
            schoolYear.pecaSetting.lapse2.ambleCoins.piggyBankSlider[1].description)

        # lapse3
        requestData = dict(
            teachersMeetingFile=(io.BytesIO(b'hi everyone'),
                                 'teachersMeetingFile3.pdf'),
            teachersMeetingDescription="Some description",
            piggyBankDescription="Some description",
            piggyBankSlider=json.dumps(
                [{"image": "http://localhost:10505/resources/images/learningmodules/5e4edc7edb90150c560b2dc1.png",
                  "description": "some description"}]
            )
        )
        res = self.client().post(
            '/pecasetting/amblecoins/3',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        res = self.client().get(
            '/pecasetting/amblecoins/3')
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual('teachersMeetingFile3.pdf',
                         result['teachersMeetingFile']['name'])

    def test_endpoint_annual_convention(self):

        requestData = dict(
            step1Description="Some 1 description",
            step2Description="Some 2 description",
            step3Description="Some 3 description",
            step4Description="Some 4 description"
        )
        res = self.client().post(
            '/pecasetting/annualconvention',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        schoolYear = SchoolYear.objects.get(id=self.schoolYear.pk)
        self.assertEqual(
            "Some 1 description",
            schoolYear.pecaSetting.lapse1.annualConvention.step1Description)
        self.assertEqual(
            "Some 2 description",
            schoolYear.pecaSetting.lapse1.annualConvention.step2Description)
        self.assertEqual(
            "Some 3 description",
            schoolYear.pecaSetting.lapse1.annualConvention.step3Description)
        self.assertEqual(
            "Some 4 description",
            schoolYear.pecaSetting.lapse1.annualConvention.step4Description)

        res = self.client().get(
            '/pecasetting/annualconvention')
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual('Some 1 description',
                         result['step1Description'])

        requestData = dict(
            step1Description="Some 1 description updated",
            step2Description="Some 2 description",
            step3Description="Some 3 description",
            step4Description="Some 4 description"
        )
        res = self.client().post(
            '/pecasetting/annualconvention',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        schoolYear = SchoolYear.objects.get(id=self.schoolYear.pk)
        self.assertEqual(
            "Some 1 description updated",
            schoolYear.pecaSetting.lapse1.annualConvention.step1Description)

    def test_endpoint_activities(self):

        # save
        requestData = dict(
            name="some name",
            hasText="true",
            hasDate="true",
            hasFile="true",
            hasVideo="true",
            hasChecklist="true",
            hasUpload="true",
            text="some text",
            file=(io.BytesIO(
                b'hi everyone'), 'activityFile.pdf'),
            video=json.dumps(
                {"name": "somename", "url": "https://youtube.com"}),
            checklist=json.dumps([{"name": "objectve 1"}]),
            approvalType="2",
            status="1"
        )
        res = self.client().post(
            '/pecasetting/activities/1',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        schoolYear = SchoolYear.objects.get(id=self.schoolYear.pk)
        self.assertEqual(
            "activityFile.pdf",
            schoolYear.pecaSetting.lapse1.activities[0].file.name)

        # update
        requestData['file'] = (io.BytesIO(
            b'hi everyone'), 'activityFileUpdated.pdf')

        res = self.client().put(
            '/pecasetting/activities/1/' +
            str(schoolYear.pecaSetting.lapse1.activities[0].id),
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        schoolYear = SchoolYear.objects.get(id=self.schoolYear.pk)
        self.assertEqual(
            "activityFileUpdated.pdf",
            schoolYear.pecaSetting.lapse1.activities[0].file.name)

        # get
        res = self.client().get(
            '/pecasetting/activities/1/'+str(schoolYear.pecaSetting.lapse1.activities[0].id))
        self.assertEqual(res.status_code, 200)

        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual('activityFileUpdated.pdf',
                         result['file']['name'])

        # delete
        res = self.client().delete(
            '/pecasetting/activities/1/'+str(schoolYear.pecaSetting.lapse1.activities[0].id))
        self.assertEqual(res.status_code, 200)

        # get deleted
        res = self.client().get(
            '/pecasetting/activities/1/'+str(schoolYear.pecaSetting.lapse1.activities[0].id))
        self.assertEqual(res.status_code, 404)

    def test_endpoint_goal_setting(self):
        requestData = dict()
        for i in range(6):
            requestData['grade'+str(i+1)] = {
                "multitplicationsPerMin": (i+1)*10,
                "operationsPerMin": (i+1)*10,
                "wordsPerMin": (i+1)*10
            }

        res = self.client().post(
            '/pecasetting/goalsetting',
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        res = self.client().get(
            '/pecasetting/goalsetting')
        self.assertEqual(res.status_code, 200)

        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(30,
                         result['grade3']['wordsPerMin'])

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')
