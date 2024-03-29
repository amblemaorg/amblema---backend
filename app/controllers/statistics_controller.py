# app/controllers/statistics_controller.py


from flask import request
from flask_restful import Resource
from flask import current_app

from app.services.statistics_service import StatisticsService
from app.services.statistics_user_service import StatisticsUserService
from app.services.statistics_diagnostics_service import StatisticsDiagnosticService
from app.services.statistics_olympics_service import StatisticsOlympicsService
from app.helpers.handler_request import getQueryParams
from app.services.statistics_active_sponsor_service import StatisticsActiveSponsorService
from app.services.statistics_inactive_sponsor_service import StatisticsInactiveSponsorService
from app.services.statistics_number_active_schools_service import StatisticsNumberActiveSchoolsService
from app.helpers.handler_authorization import jwt_required


class UserSummaryController(Resource):

    service = StatisticsService()

    @jwt_required
    def get(self):
        return self.service.get_count_users()


class UserReportController(Resource):
    service = StatisticsUserService()

    @jwt_required
    def get(self, userType):
        filters = getQueryParams(request)
        return self.service.get_users(userType, filters)


class DiagnosticReportController(Resource):

    service = StatisticsDiagnosticService()

    @jwt_required
    def get(self, schoolYearId, schoolId):
        diagnostics = None
        if request.args:
            if 'diagnostics' in request.args.keys():
                diagnostics = request.args['diagnostics']
        return self.service.get(schoolYearId, schoolId, diagnostics)


class OlympicsReportCtrl(Resource):

    service = StatisticsOlympicsService()

    @jwt_required
    def get(self, startPeriodId, endPeriodId):
        return self.service.get(startPeriodId, endPeriodId)


class ActiveSponsorsGraphicController(Resource):

    service = StatisticsActiveSponsorService()

    @jwt_required
    def get(self, startPeriodId, endPeriodId):
        return self.service.get(startPeriodId, endPeriodId)


class InactiveSponsorsGraphicController(Resource):

    service = StatisticsInactiveSponsorService()

    @jwt_required
    def get(self, startPeriodId, endPeriodId):
        return self.service.get(startPeriodId, endPeriodId)


class NumberActiveSchoolsController(Resource):

    service = StatisticsNumberActiveSchoolsService()

    @jwt_required
    def get(self, startPeriodId, endPeriodId):
        return self.service.get(startPeriodId, endPeriodId)
