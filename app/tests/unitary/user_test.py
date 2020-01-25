# app/tests/unitary/users_test.py

import unittest
import json
from app.models.user_model import UserSchema


class UserTestCase(unittest.TestCase):
    """Test case for user validations."""

    def test_name_field_only_letters(self):
        user = {
            "firstName": "greudys",
        }
        userSchema = UserSchema(partial=True)
        self.assertEqual(userSchema.validate(user),{})

        user = {
            "firstName": "3445",
        }
        userSchema = UserSchema(partial=True)
        self.assertEqual(userSchema.validate(user),{'firstName': ['Field accepts only letters']})

        user = {
            "firstName": "vngjhn--",
        }
        userSchema = UserSchema(partial=True)
        self.assertEqual(userSchema.validate(user),{'firstName': ['Field accepts only letters']})