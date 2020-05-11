# app/services/statistics_user_service.py


import json

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
from mongoengine.connection import get_db


class StatisticsUserService():

    def get_users(self, userType, status="1", instructed=None):
        users = []
        if userType == "0":
            schema = SponsorUserSchema(exclude=['projects', 'role'])
            records = SponsorUser.objects(isDeleted=False, status=status)
            if records:
                for record in records:
                    user = schema.dump(record)
                    user['schools'] = []
                    user['addressState'] = "" if not user['addressState'] else user['addressState']['name']
                    user['addressMunicipality'] = "" if not user['addressMunicipality'] else user['addressMunicipality']['name']
                    for project in record.projects:
                        if project.school:
                            user['schools'].append(project.school.name)
                    users.append(user)
        elif userType == "1":
            schema = CoordinatorUserSchema(exclude=['projects', 'role'])
            if instructed:
                instructed = instructed == "true"
                records = CoordinatorUser.objects(
                    isDeleted=False, status=status, instructed=instructed)
            else:
                records = CoordinatorUser.objects(
                    isDeleted=False, status=status)
            if records:
                for record in records:
                    user = schema.dump(record)
                    user['schools'] = []
                    user['addressState'] = "" if not user['addressState'] else user['addressState']['name']
                    user['addressMunicipality'] = "" if not user['addressMunicipality'] else user['addressMunicipality']['name']
                    for project in record.projects:
                        if project.school:
                            user['schools'].append(project.school.name)
                    users.append(user)
        elif userType == "2":
            schema = SchoolUserSchema(exclude=['project', 'role'])
            records = SchoolUser.objects(isDeleted=False, status=status)
            if records:
                for record in records:
                    user = schema.dump(record)
                    user['addressState'] = "" if not user['addressState'] else user['addressState']['name']
                    user['addressMunicipality'] = "" if not user['addressMunicipality'] else user['addressMunicipality']['name']
                    users.append(user)
        elif userType == "3":
            schema = TeacherSchema()
            schoolYear = SchoolYear.objects(
                isDeleted=False, status="1").only('id').first()
            pecas = PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False).only(
                'school__teachers')
            records = []
            for peca in pecas:
                for teacher in peca.school.teachers:
                    if not teacher.isDeleted and teacher.status == status:
                        records.append(teacher)
            if records:
                for record in records:
                    user = schema.dump(record)
                    user['addressState'] = "" if not user['addressState'] else user['addressState']['name']
                    user['addressMunicipality'] = "" if not user['addressMunicipality'] else user['addressMunicipality']['name']
                    users.append(user)
        return {'typeUser': userType, 'users': users}, 200
