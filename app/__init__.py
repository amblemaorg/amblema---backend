# /app/__init__.py

import os

from flask import Flask
from flask_cors import CORS
from flask_mongoengine import MongoEngine
from flask_jwt_extended import JWTManager
from flask_compress import Compress

from app.helpers.error_helpers import CustomApi
from instance.config import app_config
from app.helpers.error_helpers import (
    RegisterNotFound, handleNotFound, CSTM_Exception)
from app.controllers.state_controller import (
    StateController, StateHandlerController)
from app.controllers.municipality_controller import (
    MunicipalityController, MunicipalityHandlerController)
from app.controllers.role_controller import (
    RoleController, RoleHandlerController
)
from app.controllers.entity_controller import (
    EntityController, EntityHandlerController
)
from app.controllers.user_controller import (
    UserController, UserHandlerController
)
from app.controllers.learning_module_controller import (
    LearningController,
    LearningHandlerController,
    AnswerLearningModuleController
)
from app.controllers.school_year_controller import (
    SchoolYearController, SchoolYearHandlerController, EnrollCtrl, EnrollSchoolsCtrl, CronScrollYearCtrl, CronEmptySchoolCtrl, CronDiagnisticosCtrl, CronAddDiagnosticsCtrl
)
from app.controllers.step_controller import (
    StepController, StepHandlerController
)
from app.controllers.school_contact_controller import (
    SchoolContactController, SchoolContactHandlerController
)
from app.controllers.sponsor_contact_controller import (
    SponsorContactController, SponsorContactHandlerController
)
from app.controllers.coordinator_contact_controller import (
    CoordinatorContactController, CoordinatorContactHandlerController
)
from app.controllers.project_controller import (
    ProjectController, ProjectHandlerController,
    ProjectStepsController, ProjectPecaController
)
from app.controllers.request_find_coordinator_controller import (
    ReqFindCoordController, ReqFindCoordHandlerController
)
from app.controllers.request_find_spondor_controller import (
    ReqFindSponsorController, ReqFindSponsorHandlerController
)
from app.controllers.request_find_school_controller import (
    ReqFindSchoolController, ReqFindSchoolHandlerController
)
from app.controllers.peca_setting_controller import (
    PecaSettingController
)
from app.controllers.initial_workshop_controller import (
    InitialWorkshopController
)
from app.controllers.lapse_planning_controller import (
    LapsePlanningController
)
from app.controllers.amblecoin_controller import (
    AmbleCoinController
)
from app.controllers.annual_convention_controller import (
    AnnualConventionController
)
from app.controllers.annual_preparation_controller import (
    AnnualPreparationController
)
from app.controllers.environmental_project_controller import (
    EnvironmentalProjectController
)
from app.controllers.request_step_approval_controller import (
    ReqStepApprovalController
)
from app.controllers.request_project_approval_controller import (
    ReqProjectApprovalController, ReqProjectApprovalHandlerController
)
from app.controllers.request_content_approval_controller import (
    ReqContentApprovalController, ReqContentApprovalHandlerController)
from app.controllers.request_all_controller import (
    ReqContactAllController, ReqFindAllController)
from app.controllers.activity_controller import (
    ActivityController, ActivityHandlerController, ActivitySummaryController
)
from app.controllers.goal_setting_controller import (
    GoalSettingController
)
from app.controllers.peca_project_controller import (
    PecaProjectController,
    PecaProjectHandlerController
)
from app.controllers.peca_project_print_controller import PecaProjectHandlerPrintOptionsController
from app.controllers.peca_school_controller import SchoolController
from app.controllers.peca_activities_slider_controller import ActivitiesSliderController
from app.controllers.peca_amblecoins_controller import (
    PecaAmblecoinsController, PecaAmbleSectionCtrl
)
from app.controllers.peca_olympics_controller import (
    PecaOlympicsController, PecaOlympicsHandlerCtrl
)
from app.controllers.peca_annual_preparation_controller import (
    PecaPreparationController, PecaPreparationHandlerCtrl
)
from app.controllers.peca_environmental_project_controller import PecaEnvironmentalProjectCtrl
from app.controllers.peca_annual_convention_controller import (
    PecaConventionController
)
from app.controllers.peca_lapse_planning_controller import (
    PecaLapsePlanningCtrl
)
from app.controllers.peca_initial_workshop_controller import (
    PecaInitialWorkshopCtrl
)
from app.controllers.peca_activities_controller import (
    PecaActivitiesCtrl, CronPecaActivitiesCtrl, ReportActivitiesCtrl
)
from app.controllers.peca_schedule_controller import (
    ScheduleController
)
from app.controllers.teacher_controller import (
    TeacherController, TeacherHandlerController
)
from app.controllers.section_controller import(
    SectionController, SectionHandlerController, SectionExportController
)
from app.controllers.student_controller import (
    StudentController, StudentHandlerController
)
from app.controllers.statistics_controller import (
    UserSummaryController, DiagnosticReportController, UserReportController, OlympicsReportCtrl, ActiveSponsorsGraphicController, InactiveSponsorsGraphicController, NumberActiveSchoolsController
)
from app.controllers.diagnostic_controller import DiagnosticController
from app.controllers.teacher_testimonial_controller import (
    TeacherTestimonialController
)
from app.controllers.peca_special_lapse_activity_controller import (
    PecaSpecialActivityController
)
from app.controllers.peca_yearbook_controller import PecaYearbookController
from app.controllers.monitoring_activities_controller import (
    MonitoringActivitiesController
)
from app.controllers.cron_emails_lost_controller import CronEmailsLostController
from app.controllers.cron_student_controller import CronStudentController
from app.controllers.promote_student_controller import PromoteStudentController, SectionsPromoteStudentController, PromoteStudentsController, ChangeSectionStudentsController
from app.controllers.specialty_teacher_controller import (
    SpecialtyTeacherController, SpecialtyTeacherHandlerController
)

from app.controllers.peca_grade_controller import PecaGradeController

db = MongoEngine()
compress = Compress()


def create_app(config_instance):

    app = Flask(__name__)
    app.config.from_object(app_config[config_instance])
    db.init_app(app)
    CORS(app)
    jwt = JWTManager(app)
    compress.init_app(app)

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
        '/roles',
        '/roles/'
    )
    api.add_resource(
        RoleHandlerController,
        '/roles/<string:roleId>',
        '/roles/<string:roleId>/'
    )
    api.add_resource(
        UserController,
        '/users',
        '/users/'
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
        AnswerLearningModuleController,
        '/answerlearningmodule/<string:id>',
        '/answerlearningmodule/<string:id>/'
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
    api.add_resource(EnrollCtrl, '/enrollment/<string:projectId>')
    api.add_resource(EnrollSchoolsCtrl, '/enrollment')
    api.add_resource(SchoolContactController, '/schoolscontacts')
    api.add_resource(SchoolContactHandlerController,
                     '/schoolscontacts/<string:id>')
    api.add_resource(SponsorContactController, '/sponsorscontacts')
    api.add_resource(SponsorContactHandlerController,
                     '/sponsorscontacts/<string:id>')
    api.add_resource(CoordinatorContactController, '/coordinatorscontacts')
    api.add_resource(CoordinatorContactHandlerController,
                     '/coordinatorscontacts/<string:id>')
    api.add_resource(ProjectController, '/projects')
    api.add_resource(ProjectHandlerController, '/projects/<string:id>')
    api.add_resource(ProjectStepsController, '/projectsteps/<string:id>')
    api.add_resource(ProjectPecaController, '/projectpeca/<string:id>')
    api.add_resource(ReqFindCoordController, '/requestsfindcoordinator')
    api.add_resource(ReqFindCoordHandlerController,
                     '/requestsfindcoordinator/<string:id>')
    api.add_resource(ReqFindSponsorController, '/requestsfindsponsor')
    api.add_resource(ReqFindSponsorHandlerController,
                     '/requestsfindsponsor/<string:id>')
    api.add_resource(ReqFindSchoolController, '/requestsfindschool')
    api.add_resource(ReqFindSchoolHandlerController,
                     '/requestsfindschool/<string:id>')
    api.add_resource(PecaSettingController, '/pecasetting')
    api.add_resource(InitialWorkshopController,
                     '/pecasetting/initialworkshop/<string:lapse>')
    api.add_resource(LapsePlanningController,
                     '/pecasetting/lapseplanning/<string:lapse>')
    api.add_resource(AmbleCoinController,
                     '/pecasetting/amblecoins/<string:lapse>')
    api.add_resource(AnnualConventionController,
                     '/pecasetting/annualconvention/<string:lapse>')
    api.add_resource(AnnualPreparationController,
                     '/pecasetting/annualpreparation/<string:lapse>')
    api.add_resource(EnvironmentalProjectController,
                     '/pecasetting/environmentalproject')
    api.add_resource(ActivitySummaryController,
                     '/pecasetting/activities')
    api.add_resource(ActivityController,
                     '/pecasetting/activities/<string:lapse>')
    api.add_resource(ActivityHandlerController,
                     '/pecasetting/activities/<string:id>/<string:lapse>')
    api.add_resource(GoalSettingController, '/pecasetting/goalsetting')
    api.add_resource(ReqStepApprovalController, '/requestsstepapproval')
    api.add_resource(ReqProjectApprovalController, '/requestsprojectapproval')
    api.add_resource(ReqProjectApprovalHandlerController,
                     '/requestsprojectapproval/<string:id>')
    api.add_resource(ReqContactAllController, '/contactrequests')
    api.add_resource(ReqFindAllController, '/findrequests')
    api.add_resource(PecaProjectController, '/pecaprojects')
    api.add_resource(PecaProjectHandlerController, '/pecaprojects/<string:id>')
    api.add_resource(PecaProjectHandlerPrintOptionsController, '/pecaprojects/<string:id>/printoptions')
    api.add_resource(ReqContentApprovalController,
                     '/requestscontentapproval')
    api.add_resource(ReqContentApprovalHandlerController,
                     '/requestscontentapproval/<string:id>')
    api.add_resource(TeacherController,
                     '/schools/teachers/<string:schoolId>')
    api.add_resource(TeacherHandlerController,
                     '/schools/teachers/<string:schoolId>/<string:teacherId>')
    api.add_resource(SchoolController,
                     '/pecaprojects/school/<string:pecaId>')
    api.add_resource(ActivitiesSliderController,
                     '/pecaprojects/activitiesslider/<string:pecaId>')
    api.add_resource(SectionController,
                     '/pecaprojects/sections/<string:pecaId>')
    api.add_resource(SectionHandlerController,
                     '/pecaprojects/sections/<string:pecaId>/<string:sectionId>')
    api.add_resource(StudentController,
                     '/pecaprojects/students/<string:pecaId>/<string:sectionId>')
    api.add_resource(StudentHandlerController,
                     '/pecaprojects/students/<string:pecaId>/<string:sectionId>/<string:studentId>')
    api.add_resource(DiagnosticController,
                     '/pecaprojects/diagnostics/<string:diagnostic>/<string:lapse>/<string:pecaId>/<string:sectionId>/<string:studentId>')
    api.add_resource(PecaAmblecoinsController,
                     '/pecaprojects/amblecoins/<string:pecaId>/<string:lapse>')
    api.add_resource(PecaAmbleSectionCtrl,
                     '/pecaprojects/amblecoins/section/<string:pecaId>/<string:lapse>')
    api.add_resource(PecaOlympicsController,
                     '/pecaprojects/olympics/<string:pecaId>/<string:lapse>')
    api.add_resource(PecaOlympicsHandlerCtrl,
                     '/pecaprojects/olympics/<string:pecaId>/<string:lapse>/<string:studentId>')
    api.add_resource(PecaPreparationController,
                     '/pecaprojects/annualpreparation/<string:pecaId>')
    api.add_resource(PecaPreparationHandlerCtrl,
                     '/pecaprojects/annualpreparation/<string:pecaId>/<string:teacherId>')
    api.add_resource(PecaConventionController,
                     '/pecaprojects/annualconvention/<string:pecaId>')
    api.add_resource(PecaLapsePlanningCtrl,
                     '/pecaprojects/lapseplanning/<string:pecaId>/<string:lapse>')
    api.add_resource(PecaInitialWorkshopCtrl,
                     '/pecaprojects/initialworkshop/<string:pecaId>/<string:lapse>')
    api.add_resource(PecaSpecialActivityController,
                     '/pecaprojects/specialsactivities/<string:pecaId>/<string:lapse>')
    api.add_resource(PecaActivitiesCtrl,
                     '/pecaprojects/activities/<string:pecaId>/<string:lapse>/<string:activityId>')
    api.add_resource(ScheduleController,
                     '/pecaprojects/schedule/<string:pecaId>')
    api.add_resource(PecaYearbookController,
                     '/pecaprojects/yearbook/<string:pecaId>')
    api.add_resource(PecaEnvironmentalProjectCtrl,
                     '/pecaprojects/environmentalproject/<string:pecaId>')
    api.add_resource(UserSummaryController, '/statistics/usersummary')
    api.add_resource(UserReportController, '/statistics/usersreport/<string:userType>/<string:status>',
                     '/statistics/usersreport/<string:userType>')
    api.add_resource(OlympicsReportCtrl,
                     '/statistics/olympicsreport/<string:startPeriodId>/<string:endPeriodId>')
    api.add_resource(DiagnosticReportController,
                     '/statistics/diagnosticsreport/<string:schoolYearId>/<string:schoolId>')
    api.add_resource(ActiveSponsorsGraphicController,
                     '/statistics/activesponsorsgraphic/<string:startPeriodId>/<string:endPeriodId>')
    api.add_resource(InactiveSponsorsGraphicController,
                     '/statistics/inactivesponsorsgraphic/<string:startPeriodId>/<string:endPeriodId>')
    api.add_resource(NumberActiveSchoolsController,
                     '/statistics/numberactiveschools/<string:startPeriodId>/<string:endPeriodId>')
    api.add_resource(TeacherTestimonialController,
                     '/schools/teacherstestimonials/<string:schoolId>')
    api.add_resource(MonitoringActivitiesController,
                     '/pecasetting/monitoringactivities')
    api.add_resource(CronScrollYearCtrl,
                    '/cron/statistics/schoolYear')
    api.add_resource(CronStudentController, '/cron/student/<int:limit>/<int:skip>')
    api.add_resource(PromoteStudentController, '/promote/students/<school_code>/<id_section>')
    api.add_resource(SectionsPromoteStudentController, '/init/promote/students/<school_code>')
    api.add_resource(PromoteStudentsController, '/promote/students/<school_code>')
    api.add_resource(ChangeSectionStudentsController, '/students/change/section/<pecaId>')
    api.add_resource(CronEmptySchoolCtrl, '/cron/schools/empty')

    api.add_resource(SectionExportController, '/section/load/<pecaId>')
    api.add_resource(CronPecaActivitiesCtrl, '/cron/activities/percent/<int:limit>/<int:skip>')
    api.add_resource(ReportActivitiesCtrl, '/report/activities')
    api.add_resource(SpecialtyTeacherController,
                     '/specialty')
    api.add_resource(SpecialtyTeacherHandlerController,
                     '/specialty/<string:specialtyId>')
    api.add_resource(CronDiagnisticosCtrl, '/cron/diagnosticos/<int:limit>/<int:skip>')

    api.add_resource(CronAddDiagnosticsCtrl, '/cron/diagonisticos/add/<int:limit>/<int:skip>')
    
    api.add_resource(PecaGradeController, '/peca/grade/<pecaId>')

    
    return app
