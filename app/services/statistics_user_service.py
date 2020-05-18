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
from app.schemas.peca_project_schema import TeacherSchema
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
                schoolYear = SchoolYear.objects(
                    isDeleted=False, status="1").only('id').first()
                pecas = PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False).only(
                    'school__teachers')
                records = []
                for peca in pecas:
                    for teacher in peca.school.teachers:
                        available = True
                        if teacher.isDeleted:
                            available = False
                        for f in filters:
                            if hasattr(teacher, f['field']) and teacher[f['field']] != f['value']:
                                available = False
                        if available:
                            teacher.pecaId = str(peca.id)
                            records.append(teacher)
            if records:
                for record in records:
                    user = usersType[userType]['schema'].dump(record)
                    if userType == "3":
                        user['pecaId'] = record.pecaId
                    user['addressState'] = "" if not user['addressState'] else user['addressState']['name']
                    user['addressMunicipality'] = "" if not user['addressMunicipality'] else user['addressMunicipality']['name']
                    if userType in ('0', '1'):
                        user['schools'] = []
                        for project in record.projects:
                            if project.school:
                                user['schools'].append(project.school.name)
                    elif userType == '2':
                        user['sponsor'] = "" if not record.project or not record.project.sponsor else record.project.sponsor.name
                        user['coordinator'] = "" if not record.project or not record.project.coordinator else record.project.coordinator.name
                    users.append(user)

        return {'typeUser': userType, 'users': users}, 200
