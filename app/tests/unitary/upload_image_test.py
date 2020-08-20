# app/tests/unitary/learning_module_test.py

import unittest
import json

from app import create_app
from app.schemas.learning_module_schema import LearningModuleSchema
from resources.images import test_image, jpgImage, pngImage
from app.helpers.handler_images import upload_image


class LearningModuleUnitaryTestCase(unittest.TestCase):
    """Test case for learning module validations."""

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        

    def test_upload_image(self):
        upload_image(test_image, 'tests')
        upload_image(jpgImage, 'tests')
        upload_image(pngImage, 'tests')

        

    
