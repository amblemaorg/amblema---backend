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
