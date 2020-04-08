# app/services/statistics_service.py


from app.models.user_model import User
from app.models.school_user_model import SchoolUser
from app.models.coordinator_user_model import CoordinatorUser
from app.models.sponsor_user_model import SponsorUser
from app.models.peca_project_model import PecaProject
from app.models.school_year_model import SchoolYear
from flask import current_app
from mongoengine.connection import get_db


class StatisticsService():

    def get_count_users(self):
        return {
            'coordinators': self.get_count_coordinator(),
            'sponsors': self.get_count_sponsor(),
            'schools': self.get_count_school(),
            'teachers': self.get_count_teacher()
        }

    def get_count_school(self):
        return SchoolUser.objects(isDeleted=False).count()

    def get_count_coordinator(self):
        return CoordinatorUser.objects(isDeleted=False).count()

    def get_count_sponsor(self):
        return SponsorUser.objects(isDeleted=False).count()

    def get_count_teacher(self):
        count = 0
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only('id').first()
        pecas = PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False).only(
            'school__teachers')
        for peca in pecas:
            for teacher in peca.school.teachers:
                if not teacher.isDeleted:
                    count += 1
        return count
