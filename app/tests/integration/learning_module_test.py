# app/tests/integration/learning_module_test.py


import unittest
import json
from copy import deepcopy

from app import create_app, db

from app.models.school_year_model import SchoolYear
from app.models.step_model import Step, Check
from app.models.coordinator_user_model import CoordinatorUser, Answer
from app.models.project_model import Project
from app.models.role_model import Role
from app.models.state_model import State, Municipality
from app.models.learning_module_model import LearningModule, Quiz


class InitialSteps(unittest.TestCase):
    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db

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

        self.learningModule = LearningModule(
            title="module for test",
            description="module description test",
            secondaryTitle="secondaryTitle",
            secondaryDescription="secondaryDescription",
            objectives=["first objective", "second objective"],
            slider=[{"url": "https://youtube.com",
                     "description": "some description", "type": "2"}],
            images=[{"image": "http://localhost:10505/resources/images/learningmodules/5e4edc7edb90150c560b2dc1.png",
                     "description": "some description"}],
            duration=3600)
        self.learningModule.quizzes.append(
            Quiz(
                question="cuantos anios vivio Matusalem?",
                optionA="120",
                optionB="100",
                optionC="700",
                optionD="960",
                correctOption="optionD")
        )
        self.learningModule.quizzes.append(
            Quiz(
                question="cual es el lema de amblema?",
                optionA="HQS",
                optionB="HP",
                optionC="HMH",
                optionD="QAS",
                correctOption="optionA")
        )
        self.learningModule.save()

    def test_coordinator_answer_module_correctly(self):

        # correct answer
        result = self.coordinator.tryAnswerLearningModule(
            self.learningModule,
            [
                Answer(
                    quizId=self.learningModule.quizzes[0].id,
                    option="optionD"),
                Answer(
                    quizId=self.learningModule.quizzes[1].id,
                    option="optionA")
            ]
        )
        self.assertEqual(result["approved"], True)
        self.assertEqual(4, self.coordinator.learning[0].score)
        self.assertEqual(4, self.coordinator.nCoins)

    def test_coordinator_answer_module_incorrectly(self):

        result = self.coordinator.tryAnswerLearningModule(
            self.learningModule,
            [
                Answer(
                    quizId=self.learningModule.quizzes[0].id,
                    option="optionB"),
                Answer(
                    quizId=self.learningModule.quizzes[1].id,
                    option="optionC")
            ]
        )
        self.assertEqual(result["approved"], False)
        self.assertEqual("2", self.coordinator.learning[0].status)
        self.assertEqual(0, self.coordinator.nCoins)

    def test_coordinator_answer_module_two_attempts(self):
        result = self.coordinator.tryAnswerLearningModule(
            self.learningModule,
            [
                Answer(
                    quizId=self.learningModule.quizzes[0].id,
                    option="optionB"),
                Answer(
                    quizId=self.learningModule.quizzes[1].id,
                    option="optionC")
            ]
        )
        self.assertEqual(result["approved"], False)

        result = self.coordinator.tryAnswerLearningModule(
            self.learningModule,
            [
                Answer(
                    quizId=self.learningModule.quizzes[0].id,
                    option="optionD"),
                Answer(
                    quizId=self.learningModule.quizzes[1].id,
                    option="optionA")
            ]
        )
        self.assertEqual(result["approved"], True)
        self.assertEqual(3, self.coordinator.learning[0].score)
        self.assertEqual(3, self.coordinator.nCoins)

    def test_coordinator_answer_module_four_attempts(self):
        for i in range(3):
            result = self.coordinator.tryAnswerLearningModule(
                self.learningModule,
                [
                    Answer(
                        quizId=self.learningModule.quizzes[0].id,
                        option="optionB"),
                    Answer(
                        quizId=self.learningModule.quizzes[1].id,
                        option="optionC")
                ]
            )
            self.assertEqual(result["approved"], False)

        result = self.coordinator.tryAnswerLearningModule(
            self.learningModule,
            [
                Answer(
                    quizId=self.learningModule.quizzes[0].id,
                    option="optionD"),
                Answer(
                    quizId=self.learningModule.quizzes[1].id,
                    option="optionA")
            ]
        )
        self.assertEqual(result["approved"], True)
        self.assertEqual(1, self.coordinator.learning[0].score)

    def test_coordinator_change_instructed_new_module(self):
        self.coordinator.instructed = True
        self.coordinator.save()

        newModule = deepcopy(self.learningModule)
        newModule.id = None
        newModule.title = "New module"
        newModule.save()

        self.coordinator = CoordinatorUser.objects.get(pk=self.coordinator.id)

        self.assertEqual(False, self.coordinator.instructed)

    def test_coordinator_delete_progress_on_delete_module(self):

        result = self.coordinator.tryAnswerLearningModule(
            self.learningModule,
            [
                Answer(
                    quizId=self.learningModule.quizzes[0].id,
                    option="optionD"),
                Answer(
                    quizId=self.learningModule.quizzes[1].id,
                    option="optionA")
            ]
        )
        self.assertEqual(result["approved"], True)
        self.assertEqual(4, self.coordinator.learning[0].score)

        self.learningModule.isDeleted = True
        self.learningModule.save()

        self.coordinator = CoordinatorUser.objects.get(pk=self.coordinator.id)
        self.assertEqual(0, len(self.coordinator.learning))

    def test_coordinator_change_instructed_on_approved(self):

        self.coordinator = CoordinatorUser.objects.get(pk=self.coordinator.id)
        self.assertEqual(False, self.coordinator.instructed)

        result = self.coordinator.tryAnswerLearningModule(
            self.learningModule,
            [
                Answer(
                    quizId=self.learningModule.quizzes[0].id,
                    option="optionD"),
                Answer(
                    quizId=self.learningModule.quizzes[1].id,
                    option="optionA")
            ]
        )
        self.assertEqual(result["approved"], True)
        self.assertEqual(4, self.coordinator.learning[0].score)

        self.coordinator = CoordinatorUser.objects.get(pk=self.coordinator.id)
        self.assertEqual(True, self.coordinator.instructed)

        newModule = deepcopy(self.learningModule)
        newModule.id = None
        newModule.title = "New module"
        newModule.save()

        self.coordinator = CoordinatorUser.objects.get(pk=self.coordinator.id)
        self.assertEqual(False, self.coordinator.instructed)

    def test_coordinator_n_coins(self):

        result = self.coordinator.tryAnswerLearningModule(
            self.learningModule,
            [
                Answer(
                    quizId=self.learningModule.quizzes[0].id,
                    option="optionD"),
                Answer(
                    quizId=self.learningModule.quizzes[1].id,
                    option="optionA")
            ]
        )
        self.assertEqual(result["approved"], True)
        self.assertEqual(4, self.coordinator.learning[0].score)

        newModule = deepcopy(self.learningModule)
        newModule.id = None
        newModule.title = "New module"
        newModule.save()

        result = self.coordinator.tryAnswerLearningModule(
            newModule,
            [
                Answer(
                    quizId=newModule.quizzes[0].id,
                    option="optionD"),
                Answer(
                    quizId=newModule.quizzes[1].id,
                    option="optionA")
            ]
        )
        self.coordinator = CoordinatorUser.objects.get(pk=self.coordinator.id)
        self.assertEqual(result["approved"], True)
        self.assertEqual(8, self.coordinator.nCoins)

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')


if __name__ == "__main__":
    unittest.main()
