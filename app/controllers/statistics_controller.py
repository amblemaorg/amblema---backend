# app/controllers/statistics_controller.py


from flask import request
from flask_restful import Resource
from flask import current_app

from app.services.statistics_service import StatisticsService
from app.services.statistics_user_service import StatisticsUserService
from app.services.statistics_diagnostics_service import StatisticsDiagnosticService
from app.helpers.handler_request import getQueryParams


class UserSummaryController(Resource):

    service = StatisticsService()

    def get(self):
        return self.service.get_count_users()


class UserReportController(Resource):
    service = StatisticsUserService()

    def get(self, userType):
        filters = getQueryParams(request)
        return self.service.get_users(userType, filters)


class DiagnosticReportController(Resource):

    service = StatisticsDiagnosticService()

    def get(self, schoolYearId, schoolId):
        diagnostics = None
        if request.args:
            if 'diagnostics' in request.args.keys():
                diagnostics = request.args['diagnostics']
        return self.service.get(schoolYearId, schoolId, diagnostics)
