# app/services/statistics_inactive_sponsor_service.py


import json
from functools import reduce
import operator

from mongoengine import Q
from flask import current_app

from app.models.sponsor_user_model import SponsorUser
from app.models.peca_project_model import PecaProject
from app.models.school_year_model import SchoolYear
from app.helpers.error_helpers import RegisterNotFound


class StatisticsInactiveSponsorService():

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
        inactiveDict = {"T1":set(), "T2":set(), "T3":set(), "T4":set()}
        
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

            for sponsor in SponsorUser.objects(isDeleted=False):
                sponsorPecas = PecaProject.objects(schoolYear=str(period.id), project__sponsor__id=str(sponsor.id))
                if not sponsorPecas:
                    for i in inactiveDict.keys():
                        inactiveDict[i].add(sponsor.id)
                else:
                    for sponsorPeca in sponsorPecas:
                        activeTup = ()
                        #Se obtiene los meses en los que estuvo activo el peca
                        if sponsorPeca.isDeleted:
                            activeTup = monthsTup[monthsTup.index(sponsorPeca.createdAt.strftime('%m')):monthsTup.index(sponsorPeca.updatedAt.strftime('%m')) + 1]
                        else:
                            activeTup = monthsTup[monthsTup.index(sponsorPeca.createdAt.strftime('%m')):]
                        
                        for i in activeTup:
                            activeDict[monthTrimesterDict[i]].add(sponsor.id)
                        
                        #Se obtiene los meses que estuvo inactivo el peca
                        diff = tuple(set(monthsTup)-set(activeTup))
                        for i in diff:
                            inactiveDict[monthTrimesterDict[i]].add(sponsor.id)

                #Calculo la diferencia de conjuntos para obtener los 
                #padrinos que realmente estan inactivos en los trimestres
                for i in inactiveDict.keys():
                        inactiveDict[i] = inactiveDict[i] - activeDict[i]

            periodDict["trimesterOne"] = len(inactiveDict["T1"])
            periodDict["trimesterTwo"] = len(inactiveDict["T2"])
            periodDict["trimesterThree"] = len(inactiveDict["T3"])
            periodDict["trimesterFour"] = len(inactiveDict["T4"])

            for i in inactiveDict.keys():
                inactiveDict[i].clear()
                activeDict[i].clear()
            
            reportData["records"].append(periodDict)

        return reportData, 200