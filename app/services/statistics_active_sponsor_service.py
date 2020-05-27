# app/services/statistics_active_sponsor_service.py


import json
from functools import reduce
import operator

from mongoengine import Q
from flask import current_app

from app.models.user_model import User
from app.models.school_user_model import SchoolUser
from app.schemas.school_user_schema import SchoolUserSchema
from app.models.coordinator_user_model import CoordinatorUser
from app.schemas.coordinator_user_schema import CoordinatorUserSchema
from app.models.sponsor_user_model import SponsorUser
from app.schemas.sponsor_user_schema import SponsorUserSchema
from app.schemas.peca_project_schema import TeacherSchema
from app.models.peca_project_model import PecaProject
from app.models.school_year_model import SchoolYear
from app.helpers.error_helpers import RegisterNotFound


class StatisticsActiveSponsorService():

    def get(self, startPeriodId, endPeriodId):

        startPeriod = SchoolYear.objects(
            id=startPeriodId, isDeleted=False).first()
        if not startPeriod:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"startPeriodId": startPeriodId})

        endPeriod = SchoolYear.objects(
            id=endPeriodId, isDeleted=False).first()
        if not endPeriod:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"endPeriodId": endPeriodId})
        
        reportData = {
            "records": []
        }