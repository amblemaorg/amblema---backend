# app/services/statistics_user_service.py


import json
from functools import reduce
import operator

from mongoengine import Q

from app.models.user_model import User
from app.models.school_user_model import SchoolUser
from app.schemas.school_user_schema import SchoolUserSchema
from app.models.coordinator_user_model import CoordinatorUser
from app.schemas.coordinator_user_schema import CoordinatorUserSchema
from app.models.sponsor_user_model import SponsorUser
from app.schemas.sponsor_user_schema import SponsorUserSchema
from app.schemas.teacher_schema import TeacherSchema
from app.models.peca_project_model import PecaProject
from app.models.school_year_model import SchoolYear
from flask import current_app


class StatisticsUserService():

    def get_users(self, userType, filters=[]):
        """
        params:
          userType: str,
          filters: ['field': str, 'value': str]
        """
        users = []
        records = []
        usersType = {
            '0': {
                'model': SponsorUser,
                'schema': SponsorUserSchema(exclude=['projects', 'role'])
            },
            '1': {
                'model': CoordinatorUser,
                'schema': CoordinatorUserSchema(exclude=['projects', 'role'])
            },
            '2': {
                'model': SchoolUser,
                'schema': SchoolUserSchema(exclude=['project', 'role'])
            },
            '3': {
                'model': SchoolYear,
                'schema': TeacherSchema()
            }
        }
        boolFilters = ('instructed', 'preregistered')
        if userType and userType in ('0', '1', '2', '3'):
            # is not a teacher
            if userType in ('0', '1', '2'):

                if filters:
                    filterList = []
                    for f in filters:
                        if f['field'] in boolFilters:
                            f['value'] = f['value'].lower() == 'true'
                        filterList.append(Q(**{f['field']: f['value']}))
                    records = usersType[userType]['model'].objects(isDeleted=False).filter(
                        reduce(operator.and_, filterList)).all()
                else:
                    records = usersType[userType]['model'].objects(
                        isDeleted=False)
            # is teacher
            else:
                records = []
                annualPreparationFilter = False
                annualPreparationTeachers = {}
                workPositionFilter = ""
                stateFilter = ""
                schoolFilter = ""
                schoolsIds = {}
                filters_availables = filters.copy()
                for f in filters:
                    if f['field'] == 'annualPreparationStatus' and f['field']:
                        annualPreparationFilter = f['value']
                        filters_availables.remove(f)
                    if f['field'] == 'workPosition' and f['field']:
                        workPositionFilter = f['value']
                        filters_availables.remove(f)
                    if f['field'] == 'state' and f['field']:
                        stateFilter = f['value']
                        filters_availables.remove(f)
                    if f['field'] == 'school' and f['field']:
                        schoolFilter = f['value']
                        filters_availables.remove(f)
                
                filters = filters_availables
                schoolYear = SchoolYear.objects(
                    isDeleted=False, status="1").only('id').first()
                if schoolFilter:    
                    pecas = PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False, project__school__id=schoolFilter).only(
                        'project__school__id',
                        'lapse1__annualPreparation',
                        'lapse2__annualPreparation',
                        'lapse3__annualPreparation')
                else:
                    pecas = PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False).only(
                        'project__school__id',
                        'lapse1__annualPreparation',
                        'lapse2__annualPreparation',
                        'lapse3__annualPreparation')
                for peca in pecas:
                    schoolsIds[peca.project.school.id] = str(peca.id)
                    for i in range(1, 4):
                        if peca['lapse{}'.format(i)].annualPreparation:
                            annualPreparation = peca['lapse{}'.format(
                                i)].annualPreparation
                            for teacher in annualPreparation.teachers:
                                annualPreparationTeachers[teacher.id] = teacher.annualPreparationStatus
                schools = SchoolUser.objects(
                    isDeleted=False, status="1", id__in=schoolsIds.keys()).only('name','teachers', 'id')
                for school in schools:
                    for teacher in school.teachers.filter(isDeleted=False):
                        available = True
                        iswork = False
                        isstate = False
                        teacher.schoolName = school.name
                        for f in filters:
                            if hasattr(teacher, f['field']) and teacher[f['field']] != f['value']:
                                available = False
                        if annualPreparationFilter and not (
                                str(teacher.id) in annualPreparationTeachers and 
                                annualPreparationTeachers[str(teacher.id)] == annualPreparationFilter
                            ):
                            available = False
                        
                        if workPositionFilter:
                            if teacher.workPosition and str(teacher.workPosition.id) == workPositionFilter:
                                iswork = True
                            else:
                                iswork = False
                        else:
                            iswork = True    
                        
                        if stateFilter:
                            if teacher.addressState and str(teacher.addressState.id) == stateFilter:
                                isstate = True
                            else:
                                isstate = False
                        else:
                            isstate = True    
                        
                        if available:
                            teacher.pecaId = schoolsIds[str(school.id)]
                            if str(teacher.id) in annualPreparationTeachers:
                                teacher.annualPreparationStatus = annualPreparationTeachers[str(teacher.id)]
                            if iswork and isstate:
                                records.append(teacher)
            if records:
                for record in records:
                    user = usersType[userType]['schema'].dump(record)
                    if userType == "3":
                        user['pecaId'] = record.pecaId
                        user["schoolName"] = record.schoolName
                    user['addressState'] = "" if not user['addressState'] else user['addressState']['name']
                    user['addressMunicipality'] = "" if not user['addressMunicipality'] else user['addressMunicipality']['name']
                    if userType in ('0', '1'):
                        user['schools'] = []
                        for project in record.projects:
                            if project.school and project.school.name:
                                user['schools'].append(project.school.name.strip())
                    elif userType == '2':
                        user['sponsor'] = "" if not record.project or not record.project.sponsor else record.project.sponsor.name
                        user['coordinator'] = "" if not record.project or not record.project.coordinator else record.project.coordinator.name
                    users.append(user)

        return {'typeUser': userType, 'users': users}, 200
