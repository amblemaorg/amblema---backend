# app/controllers/cron_emails_lost_controller.py


from flask import request
from flask_restful import Resource

from app.services.cron_emails_lost_service import EmailsLostService
from app.helpers.handler_request import getQueryParams

class CronEmailsLostController(Resource):
    service = EmailsLostService()
    def get(self):
        return self.service.run()