# app/services/statistics_active_sponsor_service.py


import json
from functools import reduce
import operator

from mongoengine import Q
from flask import current_app

from app.models.user_model import User
from app.models.school_user_model import SchoolUser
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

        sponsorMonthDict = {
            "01":set(), "02":set(), "03":set(),
            "04":set(), "05":set(), "06":set(),
            "07":set(), "08":set(), "09":set(),
            "10":set(), "11":set(), "12":set()
            }
        
        for period in SchoolYear.objects(startDate__gte=startPeriod.startDate, endDate__lte=endPeriod.endDate, isDeleted=False):
            periodDict = {
                'academicPeriodId': str(period.id),
                'academicPeriodName': period.name,
                'academicPeriodYears': [period.startDate.strftime('%Y'), period.endDate.strftime('%Y')],
                'trimesterOne': 0,
                'trimesterTwo': 0,
                'trimesterThree': 0,
                'trimesterFour': 0,
            }

            pecas = PecaProject.objects(schoolYear=period.id, isDeleted=False)

            for peca in pecas:
                if SchoolUser.objects(id=peca.project.school.id, isDeleted=False):
                    if User.objects(id=peca.project.sponsor.id, isDeleted=False):
                        month = peca.createdAt.strftime('%m')
                        sponsorMonthDict[month].add(peca.project.sponsor.id)

            periodDict["trimesterOne"] = len(sponsorMonthDict["09"] | sponsorMonthDict["10"] | sponsorMonthDict["11"])
            periodDict["trimesterTwo"] = len(sponsorMonthDict["12"] | sponsorMonthDict["01"] | sponsorMonthDict["02"])
            periodDict["trimesterThree"] = len(sponsorMonthDict["03"] | sponsorMonthDict["04"] | sponsorMonthDict["05"])
            periodDict["trimesterFour"] = len(sponsorMonthDict["06"] | sponsorMonthDict["07"]  | sponsorMonthDict["08"])

            for i in ("01","02","03","04","05","06","07","08","09","10","11","12"):
                sponsorMonthDict[i].clear()
            
            reportData["records"].append(periodDict)

        return reportData, 200