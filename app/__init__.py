# /app/__init__.py

import os

from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from flask_mongoengine import MongoEngine
from flask_jwt_extended import JWTManager

from instance.config import app_config

db = MongoEngine()


class CustomApi(Api):
    def handle_error(self, e):
        for val in current_app.error_handler_spec.values():
            for handler in val.values():
                registered_error_handlers = list(filter(lambda x: isinstance(e, x), handler.keys()))
                if len(registered_error_handlers) > 0:
                    raise e
        return super().handle_error(e)


def create_app(config_instance):

    app = Flask(__name__)
    app.config.from_object(app_config[config_instance])
    db.init_app(app)
    CORS(app)
    jwt = JWTManager(app)

    # import the authentication blueprint and register it on the app
    from app.auth import auth_blueprint
    app.register_blueprint(auth_blueprint)

    api = CustomApi(app)

    return app
