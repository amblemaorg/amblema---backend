# app/tests/unitary/handler_authorization_test.py

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask

from app.helpers import handler_authorization as auth


def user(id, role=None):
    return SimpleNamespace(id=id, role=SimpleNamespace(devName=role) if role else None)


class IsAdminTest(unittest.TestCase):

    def test_admin_roles(self):
        self.assertTrue(auth.is_admin(user("1", "superadmin")))
        self.assertTrue(auth.is_admin(user("1", "admin")))

    def test_non_admin_roles(self):
        self.assertFalse(auth.is_admin(user("1", "coordinator")))
        self.assertFalse(auth.is_admin(user("1")))
        self.assertFalse(auth.is_admin(None))


class CanManageUserTest(unittest.TestCase):

    def test_missing_users(self):
        self.assertFalse(auth.can_manage_user(None, user("2")))
        self.assertFalse(auth.can_manage_user(user("1", "admin"), None))

    def test_user_can_manage_himself(self):
        self.assertTrue(auth.can_manage_user(user("1", "school"), user("1", "school")))

    def test_non_admin_cannot_manage_others(self):
        self.assertFalse(auth.can_manage_user(user("1", "coordinator"), user("2", "school")))

    def test_admin_manages_non_superadmin(self):
        self.assertTrue(auth.can_manage_user(user("1", "admin"), user("2", "coordinator")))
        self.assertTrue(auth.can_manage_user(user("1", "admin"), user("2")))

    def test_only_superadmin_manages_superadmin(self):
        self.assertFalse(auth.can_manage_user(user("1", "admin"), user("2", "superadmin")))
        self.assertTrue(auth.can_manage_user(user("1", "superadmin"), user("2", "superadmin")))


class DecoratorsTest(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)

    def run_view(self, decorator, testing):
        self.app.config["TESTING"] = testing

        @decorator
        def view():
            return "ok", 200

        with self.app.test_request_context():
            return view()

    def test_jwt_required_skips_verification_in_testing(self):
        with patch.object(auth, "verify_jwt_in_request") as verify:
            self.assertEqual(self.run_view(auth.jwt_required, True), ("ok", 200))
            verify.assert_not_called()

    def test_jwt_required_verifies_outside_testing(self):
        with patch.object(auth, "verify_jwt_in_request") as verify:
            self.assertEqual(self.run_view(auth.jwt_required, False), ("ok", 200))
            verify.assert_called_once()

    def test_admin_required_rejects_non_admin(self):
        with patch.object(auth, "verify_jwt_in_request"), \
                patch.object(auth, "get_current_user", return_value=user("1", "school")):
            self.assertEqual(
                self.run_view(auth.admin_required, False), ({"msg": "No authorized"}, 403))

    def test_admin_required_allows_admin(self):
        with patch.object(auth, "verify_jwt_in_request"), \
                patch.object(auth, "get_current_user", return_value=user("1", "admin")):
            self.assertEqual(self.run_view(auth.admin_required, False), ("ok", 200))

    def test_admin_required_skips_checks_in_testing(self):
        with patch.object(auth, "verify_jwt_in_request") as verify:
            self.assertEqual(self.run_view(auth.admin_required, True), ("ok", 200))
            verify.assert_not_called()


class GetCurrentUserTest(unittest.TestCase):

    def test_no_identity(self):
        with patch("flask_jwt_extended.get_jwt_identity", return_value=None):
            self.assertIsNone(auth.get_current_user())
        with patch("flask_jwt_extended.get_jwt_identity", return_value={"email": "x@test.com"}):
            self.assertIsNone(auth.get_current_user())

    def test_looks_up_active_user(self):
        with patch("flask_jwt_extended.get_jwt_identity", return_value={"id": "abc"}), \
                patch("app.models.user_model.User") as User:
            User.objects.return_value.first.return_value = "usuario"
            self.assertEqual(auth.get_current_user(), "usuario")
            User.objects.assert_called_once_with(id="abc", isDeleted=False)


if __name__ == "__main__":
    unittest.main()
