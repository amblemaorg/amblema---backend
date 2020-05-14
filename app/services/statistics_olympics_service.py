# app/services/statistics_user_service.py


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


class StatisticsOlympicsService():

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
            'allPeriods': [],
            'finalScore': {
                'enrolledStudents': 0,
                'classifiedStudents': 0,
                'studentsGoldMedal': 0,
                'studentsSilverMedal': 0,
                'studentsBronzeMedal': 0
            }
        }

        periods = {}
        for period in SchoolYear.objects(startDate__gte=startPeriod.startDate, endDate__lte=endPeriod.endDate):
            periods[str(period.id)] = {
                'schoolYear': period,
                'schools': [],
                'total': {
                    'totalEnrolled': 0,
                    'totalClassified': 0,
                    'totalGoldMedals': 0,
                    'totalSilverMedals': 0,
                    'totalBronzeMedals': 0
                }
            }

        pecas = PecaProject.objects(
            schoolYear__in=periods.keys(), isDeleted=False)

        for peca in pecas:
            schoolSummary = {
                'meta': {
                    'name': peca.project.school.name,
                    'coordinator': peca.project.coordinator.name,
                    'sponsor': peca.project.sponsor.name

                },
                'grades': [],
                'total': {
                    'totalEnrolled': 0,
                    'totalClassified': 0,
                    'totalGoldMedals': 0,
                    'totalSilverMedals': 0,
                    'totalBronzeMedals': 0,
                }
            }
            grades = {}
            for i in range(1, 4):
                olympics = peca['lapse{}'.format(i)].olympics
                if olympics:
                    for student in olympics.students:
                        if student.section.grade in grades:
                            if student.section.name in grades[student.section.grade]['sections']:
                                grades[student.section.grade]['sections'][student.section.name]['inscribed'] += 1
                                if student.status == "2":
                                    grades[student.section.grade]['sections'][student.section.name]['classified'] += 1
                                    if student.result:
                                        if student.result == "1":
                                            grades[student.section.grade]['sections'][student.section.name]['medalsGold'] += 1
                                        elif student.result == "2":
                                            grades[student.section.grade]['sections'][student.section.name]['medalsSilver'] += 1
                                        elif student.result == "3":
                                            grades[student.section.grade]['sections'][student.section.name]['medalsBronze'] += 1
                            else:
                                grades[student.section.grade]['sections'][student.section.name] = {
                                    'name': student.section.name,
                                    'inscribed': 1,
                                    'classified': 1 if student.status == "2" else 0,
                                    'medalsGold': 1 if student.result == "1" else 0,
                                    'medalsSilver': 1 if student.result == "2" else 0,
                                    'medalsBronze': 1 if student.result == "3" else 0
                                }

                        else:
                            grades[student.section.grade] = {
                                'name': student.section.grade,
                                'sections': {
                                    student.section.name: {
                                        'name': student.section.name,
                                        'inscribed': 1,
                                        'classified': 1 if student.status == "2" else 0,
                                        'medalsGold': 1 if student.result == "1" else 0,
                                        'medalsSilver': 1 if student.result == "2" else 0,
                                        'medalsBronze': 1 if student.result == "3" else 0
                                    }
                                }
                            }
            for grade in grades.values():
                gradeSummary = {
                    'name': grade['name'],
                    'sections': []
                }
                for section in grade['sections'].values():
                    gradeSummary['sections'].append(section)
                    schoolSummary['total']['totalEnrolled'] += section['inscribed']
                    schoolSummary['total']['totalClassified'] += section['classified']
                    schoolSummary['total']['totalGoldMedals'] += section['medalsGold']
                    schoolSummary['total']['totalSilverMedals'] += section['medalsSilver']
                    schoolSummary['total']['totalBronzeMedals'] += section['medalsBronze']
                    periods[str(
                        peca.schoolYear.pk)]['total']['totalEnrolled'] += section['inscribed']
                    periods[str(
                        peca.schoolYear.pk)]['total']['totalClassified'] += section['classified']
                    periods[str(
                        peca.schoolYear.pk)]['total']['totalGoldMedals'] += section['medalsGold']
                    periods[str(
                        peca.schoolYear.pk)]['total']['totalSilverMedals'] += section['medalsSilver']
                    periods[str(
                        peca.schoolYear.pk)]['total']['totalBronzeMedals'] += section['medalsBronze']

                gradeSummary['sections'] = sorted(
                    gradeSummary['sections'], key=lambda x: (x['name']))

                schoolSummary['grades'].append(gradeSummary)
            schoolSummary['grades'] = sorted(
                schoolSummary['grades'], key=lambda x: (x['name']))

            periods[str(peca.schoolYear.pk)]['schools'].append(schoolSummary)

        for key in periods.keys():
            period = periods[key]
            periodSummary = {
                'academicPeriod': [
                    period['schoolYear'].startDate.strftime('%Y'),
                    period['schoolYear'].endDate.strftime('%Y')
                ],
                'schools': sorted(
                    period['schools'], key=lambda x: (x['meta']['name']))
            }
            reportData['allPeriods'].append(periodSummary)
            reportData['finalScore']['enrolledStudents'] += period['total']['totalEnrolled']
            reportData['finalScore']['classifiedStudents'] += period['total']['totalClassified']
            reportData['finalScore']['studentsGoldMedal'] += period['total']['totalGoldMedals']
            reportData['finalScore']['studentsSilverMedal'] += period['total']['totalSilverMedals']
            reportData['finalScore']['studentsBronzeMedal'] += period['total']['totalBronzeMedals']
        reportData['allPeriods'] = sorted(
            reportData['allPeriods'], key=lambda x: (x['academicPeriod'][0]))
        return reportData, 200
