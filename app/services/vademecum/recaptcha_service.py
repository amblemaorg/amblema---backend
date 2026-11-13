# -*- coding: utf-8 -*-
# app/services/vademecum/recaptcha_service.py
"""Verificación de reCAPTCHA (GES-03 4.3). Sin RECAPTCHA_SECRET_KEY se omite."""

import requests
from flask import current_app

VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
TIMEOUT_SECONDS = 5


def recaptcha_is_valid(token):
    secret = current_app.config.get("RECAPTCHA_SECRET_KEY")
    if not secret:
        return True
    if not token:
        return False
    try:
        response = requests.post(VERIFY_URL, data={"secret": secret, "response": token},
                                 timeout=TIMEOUT_SECONDS)
        return bool(response.json().get("success"))
    except Exception:  # red caída o respuesta inválida: se rechaza (falla cerrado)
        current_app.logger.exception("Vademecum: reCAPTCHA verification failed")
        return False
