# /app/__init__.py

import os

from flask import Flask
from flask_cors import CORS
from flask_mongoengine import MongoEngine
from flask_jwt_extended import JWTManager

from app.helpers.error_helpers import CustomApi
from instance.config import app_config
from app.helpers.error_helpers import (
    RegisterNotFound, handleNotFound, CSTM_Exception)
from app.controllers.state_controller import (
    StateController, StateHandlerController)
from app.controllers.municipality_controller import (
    MunicipalityController, MunicipalityHandlerController)
from app.controllers.role_controller import (
    EntityController,
    EntityHandlerController,
    RoleController,
    RoleHandlerController
)
from app.controllers.user_controller import (
    UserController, UserHandlerController
)
from app.controllers.learning_module_controller import (
    LearningController,
    LearningHandlerController,
    QuizController,
    QuizHandlerController
)
from app.controllers.school_year_controller import (
    SchoolYearController, SchoolYearHandlerController
)
from app.controllers.step_controller import (
    StepController, StepHandlerController
)
from app.controllers.diagnosis_controller import DiagnosticController
from app.controllers.school_contact_controller import (
    SchoolContactController, SchoolContactHandlerController
)
from app.controllers.sponsor_contact_controller import (
    SponsorContactController, SponsorContactHandlerController
)
from app.controllers.coordinator_contact_controller import (
    CoordinatorContactController, CoordinatorContactHandlerController
)
from app.controllers.steps_tracking_controller import (
    StepsTrackingController, StepsTrackingHandlerController
)

db = MongoEngine()


def create_app(config_instance):

    app = Flask(__name__)
    app.config.from_object(app_config[config_instance])
    db.init_app(app)
    CORS(app)
    jwt = JWTManager(app)

    app.register_error_handler(RegisterNotFound, handleNotFound)
    app.register_error_handler(CSTM_Exception, handleNotFound)

    # import the authentication blueprint and register it on the app
    from app.blueprints.auth import auth_blueprint
    from app.blueprints.web_content import web_content_blueprint
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(web_content_blueprint)

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
    api.add_resource(
        LearningController,
        '/learningmodules',
        '/learningmodules/'
    )
    api.add_resource(
        LearningHandlerController,
        '/learningmodules/<string:id>',
        '/learningmodules/<string:id>/'
    )
    api.add_resource(
        QuizController,
        '/quizzes',
        '/quizzes/'
    )
    api.add_resource(
        QuizHandlerController,
        '/quizzes/<string:id>',
        '/quizzes/<string:id>/'
    )
    api.add_resource(
        StepController,
        '/steps',
        '/steps/'
    )
    api.add_resource(
        StepHandlerController,
        '/steps/<string:id>',
        '/steps/<string:id>/'
    )
    api.add_resource(
        SchoolYearController,
        '/schoolyears',
        '/schoolyears/'
    )
    api.add_resource(
        SchoolYearHandlerController,
        '/schoolyears/<string:id>',
        '/schoolyears/<string:id>/'
    )
    api.add_resource(DiagnosticController, '/diagnosticsettings')
    api.add_resource(SchoolContactController, '/schoolscontacts')
    api.add_resource(SchoolContactHandlerController, '/schoolscontacts/<string:id>')
    api.add_resource(SponsorContactController, '/sponsorscontacts')
    api.add_resource(SponsorContactHandlerController, '/sponsorscontacts/<string:id>')
    api.add_resource(CoordinatorContactController, '/coordinatorscontacts')
    api.add_resource(CoordinatorContactHandlerController, '/coordinatorscontacts/<string:id>')
    api.add_resource(StepsTrackingController, '/stepstrackings')
    api.add_resource(StepsTrackingHandlerController, '/stepstrackings/<string:id>')


    return app
