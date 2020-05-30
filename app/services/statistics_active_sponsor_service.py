# app/services/statistics_active_sponsor_service.py


import json
from functools import reduce
import operator

from mongoengine import Q
from flask import current_app

from app.models.sponsor_user_model import SponsorUser
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

        monthTrimesterDict = {
            "09": "T1", "10": "T1", "11": "T1",
            "12": "T2", "01": "T2", "02": "T2",
            "03": "T3", "04": "T3", "05": "T3",
            "06": "T4", "07": "T4", "08": "T4"
            }

        activeDict = {"T1":set(), "T2":set(), "T3":set(), "T4":set()}
        
        monthsTup = ("09","10","11","12","01","02","03","04","05","06","07","08")
        
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

            pecas = PecaProject.objects(schoolYear=str(period.id))

            for peca in pecas:
                if SchoolUser.objects(id=str(peca.project.school.id), isDeleted=False):
                    if SponsorUser.objects(id=str(peca.project.sponsor.id), isDeleted=False):
                        activeTup = ()
                        #Se obtiene los meses en los que estuvo activo el peca
                        if peca.isDeleted:
                            activeTup = monthsTup[monthsTup.index(peca.createdAt.strftime('%m')):monthsTup.index(peca.updatedAt.strftime('%m')) + 1]
                        else:
                            activeTup = monthsTup[monthsTup.index(peca.createdAt.strftime('%m')):]
                        
                        for i in activeTup:
                            activeDict[monthTrimesterDict[i]].add(peca.project.sponsor.id)
            
            periodDict["trimesterOne"] = len(activeDict["T1"])
            periodDict["trimesterTwo"] = len(activeDict["T2"])
            periodDict["trimesterThree"] = len(activeDict["T3"])
            periodDict["trimesterFour"] = len(activeDict["T4"])

            for i in activeDict.keys():
                activeDict[i].clear()
            
            reportData["records"].append(periodDict)

        return reportData, 200