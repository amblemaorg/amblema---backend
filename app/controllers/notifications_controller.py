# app/controllers/notifications_controller.py

from flask import request
from flask_restful import Resource
from app.services.notifications_service import NotificationsService
from app.helpers.handler_authorization import jwt_required

class NotificationsPendingController(Resource):
    service = NotificationsService()

    @jwt_required
    def get(self):
        return self.service.get_pending_notifications()
