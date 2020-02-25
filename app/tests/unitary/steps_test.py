# app/tests/unitary/users_test.py

import unittest
import json
from app.schemas.step_schema import StepSchema


class UserTestCase(unittest.TestCase):
    """Test case for user validations."""

    def test_step_type_1_text(self):
        stepSchema = StepSchema(partial=True)
        step = {
            "name": "some step type 1",
            "type": "1",
            "tag": "1",
            "text": "some text for step",
            "status": "1"
        }
        self.assertEqual(stepSchema.validate(step), {})

        step["type"] = None
        self.assertEqual(stepSchema.validate(step), {
                         'type': [{'msg': 'Not allowed null', 'status': '3'}]})

    def test_step_type_2_date(self):
        stepSchema = StepSchema(partial=True)
        step = {
            "name": "some step type 1",
            "type": "2",
            "tag": "1",
            "text": "some text for step",
            "date": "2020-02-25 00:00:00",
            "status": "1"
        }
        self.assertEqual(stepSchema.validate(step), {})

    def test_step_type_3_file_or_video(self):
        stepSchema = StepSchema(partial=True)
        step = {
            "name": "some step type 1",
            "type": "3",
            "tag": "1",
            "text": "some text for step",
            "status": "1"
        }
        self.assertEqual(stepSchema.validate(step), {
                         'file': ['Field is required'], 'video': ['Field is required']})

        step = {
            "name": "some step type 1",
            "type": "3",
            "tag": "1",
            "text": "some text for step",
            "status": "1",
            "file": {"name": "some name",
                     "url": "http://somedomain.com/somefile.pdf"}
        }
        self.assertEqual(stepSchema.validate(step), {})

        step = {
            "name": "some step type 1",
            "type": "3",
            "tag": "1",
            "text": "some text for step",
            "status": "1",
            "video": {"name": "some name",
                      "url": "https://youtube.com/somefileid"}
        }
        self.assertEqual(stepSchema.validate(step), {})

    def test_step_type_4_date_file(self):
        stepSchema = StepSchema(partial=True)
        step = {
            "name": "some step type 1",
            "type": "4",
            "tag": "1",
            "text": "some text for step",
            "status": "1",
            "file": {
                "name": "some name",
                "url": "http://somedomain.com/somefile.pdf"
            },
            "date": "2020-02-25 00:00:00"
        }
        self.assertEqual(stepSchema.validate(step), {})

    def test_step_type_5_checklist(self):
        stepSchema = StepSchema(partial=True)
        step = {
            "name": "some step type 1",
            "type": "5",
            "tag": "1",
            "text": "some text for step",
            "status": "1",
            "checklist": [
                {"name": "to do 1"},
                {"name": "to do 2"},
                {"name": "to do 3"}
            ]
        }
        self.assertEqual(stepSchema.validate(step), {})
