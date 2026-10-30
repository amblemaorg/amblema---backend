# app/tests/unitary/handler_emails_test.py

import unittest
from unittest.mock import MagicMock, patch

import requests
from flask import Flask

from app.helpers import handler_emails as emails


class EmailsTestBase(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            GMAIL_CLIENT_ID="id", GMAIL_CLIENT_SECRET="secret", GMAIL_REFRESH_TOKEN="token",
            GMAIL_FROM="amblema@test.com", GMAIL_FROM_NAME="AmbLeMa",
            SMTP_USERNAME="user", SMTP_PASSWORD="pass", SMTP_FROM="amblema@test.com",
            SMTP_HOST="smtp.test.com", SMTP_PORT="587")
        self.context = self.app.app_context()
        self.context.push()

    def tearDown(self):
        self.context.pop()


def response(status, payload=None, text=""):
    res = MagicMock(status_code=status, text=text)
    res.json.return_value = payload or {}
    return res


class SendEmailRoutingTest(EmailsTestBase):
    """send_email: Gmail primero, SMTP solo como respaldo."""

    def test_gmail_ok_skips_smtp(self):
        with patch.object(emails, 'send_email_gmail', return_value=True), \
                patch.object(emails, 'send_email_smtp') as smtp:
            self.assertTrue(emails.send_email("<p>x</p>", "x", "Asunto", "a@test.com"))
            smtp.assert_not_called()

    def test_gmail_timeout_does_not_resend_by_smtp(self):
        timeout = ({'msg': 'Gmail API Timeout', 'sent_attempted': True}, 400)
        with patch.object(emails, 'send_email_gmail', return_value=timeout), \
                patch.object(emails, 'send_email_smtp') as smtp:
            self.assertEqual(emails.send_email("b", "p", "s", "a@test.com"), timeout)
            smtp.assert_not_called()

    def test_fallback_disabled(self):
        self.app.config['DISABLE_SMTP_FALLBACK'] = True
        failure = ({'msg': 'error'}, 400)
        with patch.object(emails, 'send_email_gmail', return_value=failure), \
                patch.object(emails, 'send_email_smtp') as smtp:
            self.assertEqual(emails.send_email("b", "p", "s", "a@test.com"), failure)
            smtp.assert_not_called()

    def test_gmail_failure_falls_back_to_smtp(self):
        with patch.object(emails, 'send_email_gmail', return_value=({'msg': 'error'}, 400)), \
                patch.object(emails, 'send_email_smtp', return_value=True) as smtp:
            self.assertTrue(emails.send_email("b", "p", "s", "a@test.com"))
            smtp.assert_called_once_with("b", "p", "s", "a@test.com")


class SendEmailGmailTest(EmailsTestBase):

    def test_missing_credentials(self):
        self.app.config['GMAIL_REFRESH_TOKEN'] = None
        body, status = emails.send_email_gmail("b", "p", "s", "a@test.com")
        self.assertEqual(status, 400)
        self.assertIn("GMAIL_REFRESH_TOKEN", body['msg'])

    def test_sends_message(self):
        with patch.object(emails.requests, 'post', side_effect=[
                response(200, {'access_token': 'abc'}), response(200)]) as post:
            self.assertTrue(emails.send_email_gmail("<b>Hola</b>", "Hola", "Bienvenida", "a@test.com"))
        sendCall = post.call_args_list[1]
        self.assertEqual(sendCall[1]['headers']['Authorization'], 'Bearer abc')
        self.assertTrue(sendCall[1]['json']['raw'])

    def test_invalid_refresh_token(self):
        with patch.object(emails.requests, 'post', return_value=response(400, text="invalid_grant")):
            body, status = emails.send_email_gmail("b", "p", "s", "a@test.com")
        self.assertEqual((status, body['error']), (400, "invalid_grant"))

    def test_send_error(self):
        with patch.object(emails.requests, 'post', side_effect=[
                response(200, {'access_token': 'abc'}), response(500, text="boom")]):
            body, status = emails.send_email_gmail("b", "p", "s", "a@test.com")
        self.assertEqual((status, body['error']), (400, "boom"))

    def test_timeout_marks_sent_attempted(self):
        with patch.object(emails.requests, 'post', side_effect=requests.exceptions.Timeout("lento")):
            body, status = emails.send_email_gmail("b", "p", "s", "a@test.com")
        self.assertTrue(body['sent_attempted'])


class SendEmailSmtpTest(EmailsTestBase):

    def test_missing_credentials(self):
        self.app.config['SMTP_PASSWORD'] = None
        self.assertEqual(emails.send_email_smtp("b", "p", "s", "a@test.com")[1], 400)

    def test_starttls_on_587(self):
        with patch.object(emails.smtplib, 'SMTP') as SMTP:
            server = SMTP.return_value.__enter__.return_value
            self.assertTrue(emails.send_email_smtp("b", "p", "s", "a@test.com, b@test.com"))
        SMTP.assert_called_once_with("smtp.test.com", 587, timeout=5)
        server.starttls.assert_called_once()
        server.login.assert_called_once_with("user", "pass")
        self.assertEqual(server.sendmail.call_args[0][1], ["a@test.com", "b@test.com"])

    def test_ssl_on_465(self):
        self.app.config['SMTP_PORT'] = "465"
        with patch.object(emails.smtplib, 'SMTP_SSL') as SMTP_SSL:
            self.assertTrue(emails.send_email_smtp("b", "p", "s", "a@test.com"))
        self.assertEqual(SMTP_SSL.call_args[0], ("smtp.test.com", 465))

    def test_connection_error(self):
        with patch.object(emails.smtplib, 'SMTP', side_effect=OSError("sin red")):
            body, status = emails.send_email_smtp("b", "p", "s", "a@test.com")
        self.assertEqual((status, body['msg']), (400, "sin red"))


if __name__ == "__main__":
    unittest.main()
