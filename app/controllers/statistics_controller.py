# app/controllers/statistics_controller.py


from flask import request
from flask_restful import Resource

from app.services.statistics_service import StatisticsService
from app.helpers.handler_request import getQueryParams


class UserSummaryController(Resource):

    service = StatisticsService()

    def get(self):
        return self.service.get_count_users()
