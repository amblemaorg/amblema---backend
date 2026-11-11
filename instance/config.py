# -*- coding: utf-8 -*-
# /instance/config.py

import os
from datetime import timedelta


class Config(object):
    """Parent configuration class."""
    DEBUG = True
    CSRF_ENABLED = True
    MONGODB_SETTINGS = {
        'host': os.getenv('DB_URL')
    }
    SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    SERVER_URL = os.getenv('SERVER_URL')  # for image url
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=15)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SMTP_FROM = os.getenv('SMTP_FROM')
    SMTP_HOST = os.getenv('SMTP_HOST')
    SMTP_PORT = os.getenv('SMTP_PORT')
    GMAIL_CLIENT_ID = os.getenv('GMAIL_CLIENT_ID')
    GMAIL_CLIENT_SECRET = os.getenv('GMAIL_CLIENT_SECRET')
    GMAIL_REFRESH_TOKEN = os.getenv('GMAIL_REFRESH_TOKEN')
    GMAIL_FROM = os.getenv('GMAIL_FROM')
    GMAIL_FROM_NAME = os.getenv('GMAIL_FROM_NAME')
    # Vademécum: secreto propio para los tokens de docente (distinto de JWT_SECRET_KEY),
    # URL de la web docente para los enlaces de los correos y reCAPTCHA (opcional).
    VADEMECUM_JWT_SECRET_KEY = os.getenv('VADEMECUM_JWT_SECRET_KEY')
    VADEMECUM_WEB_URL = os.getenv('VADEMECUM_WEB_URL', 'https://vademecum.amblema.org')
    RECAPTCHA_SECRET_KEY = os.getenv('RECAPTCHA_SECRET_KEY')
    # Volumen persistente de PDF e imágenes de fichas (nunca dentro de /resources, que es público)
    VADEMECUM_STORAGE_PATH = os.getenv('VADEMECUM_STORAGE_PATH')
    # Tamaño máximo de un compendio PDF subido desde el backoffice
    VADEMECUM_MAX_UPLOAD_MB = os.getenv('VADEMECUM_MAX_UPLOAD_MB', '100')
    # Procesamiento de compendios: thread (en segundo plano), inline u off (pruebas)
    VADEMECUM_PROCESSING_MODE = os.getenv('VADEMECUM_PROCESSING_MODE', 'thread')
    # Compresión de fichas con Ghostscript: binario (por defecto `gs` del PATH), ajuste
    # (/ebook; /printer si la impresión real lo pide) y tiempo máximo por ficha en segundos
    VADEMECUM_GHOSTSCRIPT = os.getenv('VADEMECUM_GHOSTSCRIPT')
    VADEMECUM_GHOSTSCRIPT_PRESET = os.getenv('VADEMECUM_GHOSTSCRIPT_PRESET', '/ebook')
    VADEMECUM_GHOSTSCRIPT_TIMEOUT = os.getenv('VADEMECUM_GHOSTSCRIPT_TIMEOUT', '300')


class TestingConfig(Config):
    """Configurations for Testing, with a separate test database."""
    # La base debe terminar en este sufijo: create_app y los tearDown lo verifican
    # antes de escribir o borrar, para no tocar nunca amblema / amblema_qa.
    TESTING_DB_SUFFIX = '_testing'
    TESTING = True
    DEBUG = True
    ENV = 'development'
    MONGODB_SETTINGS = {
        'host': os.getenv('TESTING_DB_URL')
    }
    VADEMECUM_JWT_SECRET_KEY = 'vademecum-testing-secret'
    VADEMECUM_WEB_URL = 'https://vademecum.test'
    RECAPTCHA_SECRET_KEY = None
    # Las pruebas lanzan el procesamiento a mano (inline) cuando lo necesitan
    VADEMECUM_PROCESSING_MODE = 'off'


class DevelopmentConfig(Config):
    """Configurations for Development."""
    DEBUG = True
    ENV = 'development'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)


class QaConfig(Config):
    """Configurations for Staging."""
    DEBUG = True


class StagingConfig(Config):
    """Configurations for Staging."""
    DEBUG = True


class ProductionConfig(Config):
    """Configurations for Production."""
    DEBUG = True
    TESTING = False
    JWT_COOKIE_SECURE = True

class SupportConfig(Config):
    """Configurations for Support."""
    DEBUG = True

app_config = {
    'testing': TestingConfig,
    'development': DevelopmentConfig,
    'qa': QaConfig,
    'staging': StagingConfig,
    'support': SupportConfig,
    'production': ProductionConfig,
}


def testing_database_name(host):
    """Nombre de la base de una URL mongodb:// (sin credenciales ni opciones)."""
    if not host:
        return None
    path = host.split('://', 1)[-1].split('/', 1)
    if len(path) < 2:
        return None
    return path[1].split('?', 1)[0] or None


def assert_testing_database(host):
    """Falla si la configuración de pruebas no apunta a una base *_testing."""
    name = testing_database_name(host)
    if not name or not name.endswith(TestingConfig.TESTING_DB_SUFFIX):
        raise RuntimeError(
            "TESTING_DB_URL debe apuntar a una base que termine en '{}' (actual: {})".format(
                TestingConfig.TESTING_DB_SUFFIX, name))
    return name
