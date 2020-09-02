# app/tests/unitary/users_test.py

import unittest
import json
from app.schemas.step_schema import StepSchema


class UserTestCase(unittest.TestCase):
    """Test case for user validations."""

    def test_step_with_text(self):
        stepSchema = StepSchema(partial=True)
        
        step = {
            "name": "some step type 1",
            "tag": "1",
            "hasText": True,
            "text": "some text for step",
            "status": "1"
        }
        self.assertEqual(stepSchema.validate(step), {})

    def test_step_with_date(self):
        stepSchema = StepSchema(partial=True)
        step = {
            "name": "some step type 1",
            "tag": "1",
            "hasDate": True,
            "date": "2020-02-25 00:00:00",
            "status": "1"
        }
        self.assertEqual(stepSchema.validate(step), {})

    def test_step_with_file(self):
        stepSchema = StepSchema(partial=True)

        step = {
            "name": "some step type 1",
            "tag": "1",
            "status": "1",
            "hasFile": True,
            "file": {"name": "some name",
                     "url": "http://somedomain.com/somefile.pdf"}
        }
        self.assertEqual(stepSchema.validate(step), {})

    def test_step_with_video(self):
        stepSchema = StepSchema(partial=True)

        step = {
            "name": "some step type 1",
            "tag": "1",
            "status": "1",
            "hasVideo": True,
            "video": {"name": "some name",
                      "url": "http://somedomain.com/somevideourl"}
        }
        self.assertEqual(stepSchema.validate(step), {})

    def test_step_with_video_date_file(self):
        stepSchema = StepSchema(partial=True)
        step = {
            "name": "some step type 1",
            "tag": "1",
            "status": "1",
            "hasVideo": True,
            "hasDate": True,
            "hasFile": True,
            "video": {
                "name": "some name",
                "url": "http://somedomain.com/somevideourl"
            },
            "file": {
                "name": "some name",
                "url": "http://somedomain.com/somefile.pdf"
            }
        }
        self.assertEqual(stepSchema.validate(step), {})

    def test_step_type_5_checklist(self):
        stepSchema = StepSchema(partial=True)

        step = {
            "name": "some step type 1",
            "tag": "1",
            "hasChecklist": True,
            "status": "1",
            "checklist": [
                {"name": "to do 1"},
                {"name": "to do 2"},
                {"name": "to do 3"}
            ]
        }
        self.assertEqual(stepSchema.validate(step), {})
