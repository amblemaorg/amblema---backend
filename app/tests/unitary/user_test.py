# app/tests/unitary/users_test.py

import unittest
import json
from app.models.user_model import UserSchema, AdminUserSchema


class UserTestCase(unittest.TestCase):
    """Test case for user validations."""

    def test_firstName_field_only_letters(self):
        userSchema = UserSchema(partial=True)
        user = {
            "firstName": "greudys",
        }
        self.assertEqual(userSchema.validate(user),{})
        user = {
            "firstName": "3445",
        }
        self.assertEqual(
            userSchema.validate(user),
            {'firstName': ['Field accepts only letters']})
        user = {
            "firstName": "vngjhn--",
        }
        self.assertEqual(
            userSchema.validate(user),
            {'firstName': ['Field accepts only letters']})

    def test_lastName_field_only_letters(self):
        userSchema = UserSchema(partial=True)
        user = {
            "lastName": "Godoy",
        }
        self.assertEqual(userSchema.validate(user),{})
        user = {
            "lastName": "3445",
        }
        self.assertEqual(
            userSchema.validate(user),
            {'lastName': ['Field accepts only letters']})
        user = {
            "lastName": "vngjhn--",
        }
        self.assertEqual(
            userSchema.validate(user),
            {'lastName': ['Field accepts only letters']})

    def test_cardId_field_only_numbers(self):
        userSchema = AdminUserSchema(partial=True)
        user = {
            "cardId": "20922842",
        }
        self.assertEqual(userSchema.validate(user),{})
        user = {
            "cardId": "Git",
        }
        self.assertEqual(
            userSchema.validate(user),
            {'cardId': ['Field accepts only numbers']})
        user = {
            "cardId": "123--",
        }
        self.assertEqual(
            userSchema.validate(user),
            {'cardId': ['Field accepts only numbers']})