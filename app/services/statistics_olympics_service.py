# app/services/statistics_user_service.py


import json
from functools import reduce
import operator

from bson import DBRef
from mongoengine import Q
from flask import current_app

from app.models.user_model import User
from app.models.peca_project_model import PecaProject
from app.models.school_year_model import SchoolYear
from app.helpers.error_helpers import RegisterNotFound


class StatisticsOlympicsService():

    def get(self, startPeriodId, endPeriodId, olympicsType='math'):

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
                'participantStudents': 0,
                'classifiedStudents': 0,
                'studentsGoldMedal': 0,
                'studentsSilverMedal': 0,
                'studentsBronzeMedal': 0,
                'classifiedStudentsNational': 0,
                'studentsGoldMedalNational': 0,
                'studentsSilverMedalNational': 0,
                'studentsBronzeMedalNational': 0
            }
        }

        periods = {}
        for period in SchoolYear.objects(
                isDeleted=False, startDate__gte=startPeriod.startDate, endDate__lte=endPeriod.endDate):
            periods[str(period.id)] = {
                'schoolYear': period,
                'schools': [],
                'total': {
                    'totalEnrolled': 0,
                    'totalParticipant': 0,
                    'totalClassified': 0,
                    'totalGoldMedals': 0,
                    'totalSilverMedals': 0,
                    'totalBronzeMedals': 0,
                    'totalClassifiedNational': 0,
                    'totalGoldMedalsNational': 0,
                    'totalSilverMedalsNational': 0,
                    'totalBronzeMedalsNational': 0
                }
            }

        # Raw documents with only the fields the report uses: loading the full
        # PECA documents (school with every student, lapses, yearbook) as
        # MongoEngine objects took ~25 s for eight school years
        olympicsField = 'readingOlympics' if olympicsType == 'reading' else 'olympics'
        projection = {
            'schoolYear': 1,
            'project.school.name': 1,
            'project.coordinator.name': 1,
            'project.sponsor.name': 1,
        }
        for i in range(1, 4):
            for field in ('section', 'statusRegional', 'result', 'statusNational', 'resultNational'):
                projection['lapse{}.{}.students.{}'.format(i, olympicsField, field)] = 1
        pecas = PecaProject._get_collection().find(
            {'schoolYear': {'$in': [period['schoolYear'].id for period in periods.values()]},
             'isDeleted': False},
            projection)

        for peca in pecas:
            project = peca.get('project') or {}
            schoolYearRef = peca['schoolYear']
            schoolYearId = str(schoolYearRef.id if isinstance(schoolYearRef, DBRef) else schoolYearRef)
            schoolSummary = {
                'meta': {
                    'name': (project.get('school') or {}).get('name'),
                    'coordinator': (project.get('coordinator') or {}).get('name'),
                    'sponsor': (project.get('sponsor') or {}).get('name')

                },
                'grades': [],
                'total': {
                    'totalEnrolled': 0,
                    'totalParticipant': 0,
                    'totalClassified': 0,
                    'totalGoldMedals': 0,
                    'totalSilverMedals': 0,
                    'totalBronzeMedals': 0,
                    'totalClassifiedNational': 0,
                    'totalGoldMedalsNational': 0,
                    'totalSilverMedalsNational': 0,
                    'totalBronzeMedalsNational': 0,
                }
            }
            grades = {}
            for i in range(1, 4):
                olympics = (peca.get('lapse{}'.format(i)) or {}).get(olympicsField)

                if olympics:
                    for student in olympics.get('students') or []:
                        section = student.get('section') or {}
                        if section.get('grade') in grades:
                            if section.get('name') in grades[section.get('grade')]['sections']:
                                grades[section.get('grade')]['sections'][section.get('name')]['inscribed'] += 1
                                if student.get('statusRegional') in ["1", "2"]:
                                    grades[section.get('grade')]['sections'][section.get('name')]['participant'] += 1
                                    grades[section.get('grade')]['sections'][section.get('name')]['classified'] += 1
                                if student.get('statusRegional') == "1":
                                    if student.get('result'):
                                        if student.get('result') == "1":
                                            grades[section.get('grade')]['sections'][section.get('name')]['medalsGold'] += 1
                                        elif student.get('result') == "2":
                                            grades[section.get('grade')]['sections'][section.get('name')]['medalsSilver'] += 1
                                        elif student.get('result') == "3":
                                            grades[section.get('grade')]['sections'][section.get('name')]['medalsBronze'] += 1
                                    
                                if student.get('statusNational') in ["1", "2"]:
                                    grades[section.get('grade')]['sections'][section.get('name')]['classifiedNational'] += 1
                                if student.get('statusNational') == "1":
                                    if student.get('resultNational'):
                                        if student.get('resultNational') == "1":
                                            grades[section.get('grade')]['sections'][section.get('name')]['medalsGoldNational'] += 1
                                        elif student.get('resultNational') == "2":
                                            grades[section.get('grade')]['sections'][section.get('name')]['medalsSilverNational'] += 1
                                        elif student.get('resultNational') == "3":
                                            grades[section.get('grade')]['sections'][section.get('name')]['medalsBronzeNational'] += 1
                            else:
                                grades[section.get('grade')]['sections'][section.get('name')] = {
                                    'name': section.get('name'),
                                    'inscribed': 1,
                                    'participant': 1 if student.get('statusRegional') in ["1", "2"] else 0,
                                    'classified': 1 if student.get('statusRegional') in ["1", "2"] else 0,
                                    'medalsGold': 1 if student.get('result') == "1" and student.get('statusRegional') == "1" else 0,
                                    'medalsSilver': 1 if student.get('result') == "2" and student.get('statusRegional') == "1" else 0,
                                    'medalsBronze': 1 if student.get('result') == "3" and student.get('statusRegional') == "1" else 0,
                                    'classifiedNational': 1 if student.get('statusNational') in ["1", "2"] else 0,
                                    'medalsGoldNational': 1 if student.get('resultNational') == "1" and student.get('statusNational') == "1" else 0,
                                    'medalsSilverNational': 1 if student.get('resultNational') == "2" and student.get('statusNational') == "1" else 0,
                                    'medalsBronzeNational': 1 if student.get('resultNational') == "3" and student.get('statusNational') == "1" else 0
                                }
                        else:
                            grades[section.get('grade')] = {
                                'name': section.get('grade'),
                                'sections': {
                                    section.get('name'): {
                                        'name': section.get('name'),
                                        'inscribed': 1,
                                        'participant': 1 if student.get('statusRegional') in ["1", "2"] else 0,
                                        'classified': 1 if student.get('statusRegional') in ["1", "2"] else 0,
                                        'medalsGold': 1 if student.get('result') == "1" and student.get('statusRegional') == "1" else 0,
                                        'medalsSilver': 1 if student.get('result') == "2" and student.get('statusRegional') == "1" else 0,
                                        'medalsBronze': 1 if student.get('result') == "3" and student.get('statusRegional') == "1" else 0,
                                        'classifiedNational': 1 if student.get('statusNational') in ["1", "2"] else 0,
                                        'medalsGoldNational': 1 if student.get('resultNational') == "1" and student.get('statusNational') == "1" else 0,
                                        'medalsSilverNational': 1 if student.get('resultNational') == "2" and student.get('statusNational') == "1" else 0,
                                        'medalsBronzeNational': 1 if student.get('resultNational') == "3" and student.get('statusNational') == "1" else 0
                                    }
                                }
                            }
            for grade in grades.values():
                gradeSummary = {
                    'name': grade['name'],
                    'totalInscribed': 0,
                    'totalParticipant': 0,
                    'totalClassified': 0,
                    'totalGoldMedals': 0,
                    'totalSilverMedals': 0,
                    'totalBronzeMedals': 0,
                    'totalClassifiedNational': 0,
                    'totalGoldMedalsNational': 0,
                    'totalSilverMedalsNational': 0,
                    'totalBronzeMedalsNational': 0,
                    'sections': []
                }
                for section in grade['sections'].values():
                    gradeSummary['sections'].append(section)
                    gradeSummary['totalInscribed'] += section['inscribed']
                    gradeSummary['totalParticipant'] += section.get('participant', 0)
                    gradeSummary['totalClassified'] += section['classified']
                    gradeSummary['totalGoldMedals'] += section['medalsGold']
                    gradeSummary['totalSilverMedals'] += section['medalsSilver']
                    gradeSummary['totalBronzeMedals'] += section['medalsBronze']
                    gradeSummary['totalClassifiedNational'] += section['classifiedNational']
                    gradeSummary['totalGoldMedalsNational'] += section['medalsGoldNational']
                    gradeSummary['totalSilverMedalsNational'] += section['medalsSilverNational']
                    gradeSummary['totalBronzeMedalsNational'] += section['medalsBronzeNational']

                    schoolSummary['total']['totalEnrolled'] += section['inscribed']
                    schoolSummary['total']['totalParticipant'] += section.get('participant', 0)
                    schoolSummary['total']['totalClassified'] += section['classified']
                    schoolSummary['total']['totalGoldMedals'] += section['medalsGold']
                    schoolSummary['total']['totalSilverMedals'] += section['medalsSilver']
                    schoolSummary['total']['totalBronzeMedals'] += section['medalsBronze']
                    schoolSummary['total']['totalClassifiedNational'] += section['classifiedNational']
                    schoolSummary['total']['totalGoldMedalsNational'] += section['medalsGoldNational']
                    schoolSummary['total']['totalSilverMedalsNational'] += section['medalsSilverNational']
                    schoolSummary['total']['totalBronzeMedalsNational'] += section['medalsBronzeNational']
                    periods[schoolYearId]['total']['totalEnrolled'] += section['inscribed']
                    periods[schoolYearId]['total']['totalParticipant'] += section.get('participant', 0)
                    periods[schoolYearId]['total']['totalClassified'] += section['classified']
                    periods[schoolYearId]['total']['totalGoldMedals'] += section['medalsGold']
                    periods[schoolYearId]['total']['totalSilverMedals'] += section['medalsSilver']
                    periods[schoolYearId]['total']['totalBronzeMedals'] += section['medalsBronze']
                    periods[schoolYearId]['total']['totalClassifiedNational'] += section['classifiedNational']
                    periods[schoolYearId]['total']['totalGoldMedalsNational'] += section['medalsGoldNational']
                    periods[schoolYearId]['total']['totalSilverMedalsNational'] += section['medalsSilverNational']
                    periods[schoolYearId]['total']['totalBronzeMedalsNational'] += section['medalsBronzeNational']

                gradeSummary['sections'] = sorted(
                    gradeSummary['sections'], key=lambda x: (x['name']))

                schoolSummary['grades'].append(gradeSummary)
            schoolSummary['grades'] = sorted(
                schoolSummary['grades'], key=lambda x: (x['name']))

            if schoolSummary['grades']:
                periods[schoolYearId]['schools'].append(
                    schoolSummary)

        for key in periods.keys():
            period = periods[key]
            if period['schools']:
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
                reportData['finalScore']['participantStudents'] += period['total']['totalParticipant']
                reportData['finalScore']['classifiedStudents'] += period['total']['totalClassified']
                reportData['finalScore']['studentsGoldMedal'] += period['total']['totalGoldMedals']
                reportData['finalScore']['studentsSilverMedal'] += period['total']['totalSilverMedals']
                reportData['finalScore']['studentsBronzeMedal'] += period['total']['totalBronzeMedals']
                reportData['finalScore']['classifiedStudentsNational'] += period['total']['totalClassifiedNational']
                reportData['finalScore']['studentsGoldMedalNational'] += period['total']['totalGoldMedalsNational']
                reportData['finalScore']['studentsSilverMedalNational'] += period['total']['totalSilverMedalsNational']
                reportData['finalScore']['studentsBronzeMedalNational'] += period['total']['totalBronzeMedalsNational']
        reportData['allPeriods'] = sorted(
            reportData['allPeriods'], key=lambda x: (x['academicPeriod'][0]))
        return reportData, 200
