# /app/__init__.py

import os

from flask import Flask
from flask_cors import CORS
from flask_mongoengine import MongoEngine
from flask_jwt_extended import JWTManager

from app.helpers.error_helpers import CustomApi
from instance.config import app_config
from app.helpers.error_helpers import RegisterNotFound, handleNotFound
from app.controllers.state_controller import (
    StateController,
    StateHandlerController)
from app.controllers.municipality_controller import (
    MunicipalityController,
    MunicipalityHandlerController)
from app.controllers.role_controller import (
    EntityController,
    EntityHandlerController,
    RoleController,
    RoleHandlerController
)
from app.controllers.user_controller import (
    UserController,
    UserHandlerController
)


db = MongoEngine()


def create_app(config_instance):

    app = Flask(__name__)
    app.config.from_object(app_config[config_instance])
    db.init_app(app)
    CORS(app)
    jwt = JWTManager(app)

    app.register_error_handler(RegisterNotFound, handleNotFound)

    # import the authentication blueprint and register it on the app
    from app.auth import auth_blueprint
    app.register_blueprint(auth_blueprint)

    api = CustomApi(app)
    api.add_resource(
        StateController,
        '/states',
        '/states/')
    api.add_resource(
        StateHandlerController,
        '/states/<string:stateId>',
        '/states/<string:stateId>/')
    api.add_resource(
        MunicipalityController,
        '/municipalities',
        '/municipalities/')
    api.add_resource(
        MunicipalityHandlerController,
        '/municipalities/<string:municipalityId>',
        '/municipalities/<string:municipalityId>/')
    api.add_resource(
        EntityController,
        '/entities',
        '/entities/'
    )
    api.add_resource(
        EntityHandlerController,
        '/entities/<string:entityId>',
        '/entities/<string:entityId>/'
    )
    api.add_resource(
        RoleController,
        '/roles/',
        '/roles'
    )
    api.add_resource(
        RoleHandlerController,
        '/roles/<string:roleId>',
        '/roles/<string:roleId>/'
    )
    api.add_resource(
        UserController,
        '/users/',
        '/users'
    )
    api.add_resource(
        UserHandlerController,
        '/users/<string:userId>',
        '/users/<string:userId>/'
    )

    return app
