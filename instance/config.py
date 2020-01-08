# /instance/config.py

import os
from datetime import timedelta


class Config(object):
    """Parent configuration class."""
    DEBUG = False
    CSRF_ENABLED = True
    MONGODB_SETTINGS = {
        'host': os.getenv('DB_URL')
    }
    SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    SERVER_URL = os.getenv('SERVER_URL') # for image url
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=15)
    JWT_TOKEN_LOCATION = ['cookies']
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = True


class TestingConfig(Config):
    """Configurations for Testing, with a separate test database."""
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
    DEBUG = False
    TESTING = False
    JWT_COOKIE_SECURE = True


app_config = {
    'testing': TestingConfig,
    'development': DevelopmentConfig,
    'qa': QaConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
}
