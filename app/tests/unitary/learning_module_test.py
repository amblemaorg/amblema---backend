# app/tests/unitary/learning_module_test.py

import unittest
import json

from app import create_app
from app.schemas.learning_module_schema import LearningModuleSchema
from resources.images import test_image


class LearningModuleUnitaryTestCase(unittest.TestCase):
    """Test case for learning module validations."""

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        self.schema = LearningModuleSchema(partial=True)

    def test_name_length(self):
        largeName = ""
        for i in range(61):
            largeName += "x"
        module = {
            "name": largeName
        }
        self.assertEqual(self.schema.validate(module)["name"],
                         [{"status": "13", "msg": "Invalid length"}])

    def test_title_length(self):
        largeField = ""
        for i in range(141):
            largeField += "x"
        module = {
            "title": largeField
        }
        self.assertEqual(self.schema.validate(module)["title"],
                         [{"status": "13", "msg": "Invalid length"}])

    def test_description_length(self):
        largeName = ""
        for i in range(2801):
            largeName += "x"
        module = {
            "description": largeName
        }
        self.assertEqual(self.schema.validate(module)["description"],
                         [{"status": "13", "msg": "Invalid length"}])

    def test_objectives_length(self):
        largeName = ""
        for i in range(874):
            largeName += "x"
        module = {
            "objectives": [largeName]
        }
        self.assertEqual(self.schema.validate(module)["objectives"],
                         {0: [{'msg': 'Invalid length', 'status': '13'}]})

    def test_slider_length(self):
        slider = []
        for i in range(5):
            slider.append({"url": "http://someimage.png",
                           "description": "some desc"})
        module = {
            "slider": slider
        }
        self.assertEqual(self.schema.validate(module)["slider"],
                         [{'msg': 'Invalid length', 'status': '13'}])

    def test_image_size(self):
        slider = []
        for i in range(1):
            slider.append({"url": test_image,
                           "description": "some desc"})
        module = {
            "slider": slider
        }
        self.assertEqual(self.schema.validate(module)["slider"],
                         {0: {'url': {'msg': 'Invalid image size. Max allowed 800 KB', 'status': '13'}}})

    def test_slider_description_length(self):
        largeName = ""
        for i in range(72):
            largeName += "x"
        module = {
            "slider": [{"url": "http://someimage.png", "description": largeName}]
        }
        self.assertEqual(self.schema.validate(module)["slider"],
                         {0: {'description': [{'status': '13', 'msg': 'Invalid length'}]}})

    def test_secondary_title_length(self):
        largeField = ""
        for i in range(141):
            largeField += "x"
        module = {
            "secondaryTitle": largeField
        }
        self.assertEqual(self.schema.validate(module)["secondaryTitle"],
                         [{"status": "13", "msg": "Invalid length"}])

    def test_secondary_description_length(self):
        largeField = ""
        for i in range(4971):
            largeField += "x"
        module = {
            "secondaryDescription": largeField
        }
        self.assertEqual(self.schema.validate(module)["secondaryDescription"],
                         [{"status": "13", "msg": "Invalid length"}])

    def test_images_description_length(self):
        largeName = ""
        for i in range(57):
            largeName += "x"
        module = {
            "images": [{"image": "http://someimage.png", "description": largeName}]
        }
        self.assertEqual(self.schema.validate(module)["images"],
                         {0: {'description': [{'status': '13', 'msg': 'Invalid length'}]}})

    def test_quiz_length(self):
        largeQuestion = ""
        for i in range(117):
            largeQuestion += "x"
        largeOption = ""
        for i in range(133):
            largeOption += "x"
        module = {
            "quizzes": [
                {
                    "question": largeQuestion,
                    "optionA": largeOption,
                    "optionB": largeOption[:1],
                    "optionC": largeOption[:1],
                    "optionD": largeOption[:1],
                    "correctOption": "optionA"
                }
            ]
        }
        self.assertEqual(
            self.schema.validate(module)["quizzes"],
            {0: {
                'question': [{'status': '13', 'msg': 'Invalid length'}],
                'optionA': [{'status': '13', 'msg': 'Invalid length'}]
            }
            })

        module = {}
        module['quizzes'] = []

        for i in range(16):
            module['quizzes'].append(
                {
                    "question": largeQuestion[:1],
                    "optionA": largeOption[:1],
                    "optionB": largeOption[:1],
                    "optionC": largeOption[:1],
                    "optionD": largeOption[:1],
                    "correctOption": "optionA"
                }
            )
        self.assertEqual(
            self.schema.validate(module)["quizzes"],
            [{'status': '13', 'msg': 'Invalid length'}])
