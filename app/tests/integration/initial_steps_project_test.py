# app/tests/integration/request_find_school_test.py


import unittest
import json

from app import create_app, db

from app.models.school_year_model import SchoolYear
from app.models.step_model import Step, File
from app.models.coordinator_user_model import CoordinatorUser
from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.project_model import Project
from app.models.role_model import Role
from app.models.state_model import State, Municipality
from app.models.request_find_school_model import RequestFindSchool
from app.models.request_find_sponsor_model import RequestFindSponsor
from app.models.request_find_coordinator_model import RequestFindCoordinator


class InitialSteps(unittest.TestCase):
    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db

        self.schoolYear = SchoolYear(
            name="Test",
            startDate="2020-02-14",
            endDate="2020-09-14")
        self.schoolYear.save()

        for i in range(2):
            generalStep = Step(
                name="step {}".format(str(i)),
                text="step description {}".format(str(i)),
                type="1",
                tag="1"
            )
            generalStep.save()
        for i in range(5):
            schoolStep = Step(
                name="step {}".format(str(i)),
                text="step description {}".format(str(i)),
                type="1",
                tag="2"
            )
            schoolStep.save()
        for i in range(4):
            sponsorStep = Step(
                name="step {}".format(str(i)),
                text="step description {}".format(str(i)),
                type="1",
                tag="3"
            )
            sponsorStep.save()
        for i in range(5):
            coordinatorStep = Step(
                name="step {}".format(str(i)),
                text="step description {}".format(str(i)),
                type="1",
                tag="4"
            )
            coordinatorStep.save()

        self.role = Role(name="test")
        self.role.save()

        self.state = State(
            name="Lara"
        )
        self.state.save()

        self.municipality = Municipality(
            state=self.state,
            name="Iribarren"
        )
        self.municipality.save()

        self.coordinator = CoordinatorUser(
            firstName="Test",
            lastName="Test",
            cardType="1",
            cardId="20922842",
            birthdate="1993-09-08",
            homePhone="02343432323",
            addressHome="House 34A",
            email="testemail@test.com",
            password="12345678",
            userType="2",
            phone="02322322323",
            role=self.role,
            addressState=self.state,
            addressMunicipality=self.municipality
        )
        self.coordinator.save()

    def test_create_initial_steps_on_create_project(self):

        self.project = Project(
            schoolYear=self.schoolYear,
            coordinator=self.coordinator
        )
        self.project.save()

        self.assertEqual(16, len(self.project.stepsProgress.steps))

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')


if __name__ == "__main__":
    unittest.main()
