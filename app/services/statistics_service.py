# app/services/statistics_service.py


from app.models.user_model import User
from app.models.school_user_model import SchoolUser
from app.models.coordinator_user_model import CoordinatorUser
from app.models.sponsor_user_model import SponsorUser
from app.models.peca_project_model import PecaProject
from flask import current_app
from mongoengine.connection import get_db
from app.models.school_year_model import SchoolYear


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
        schools = SchoolUser.objects(
            isDeleted=False, status="1").only('teachers')
        for school in schools:
            count += len(school.teachers.filter(isDeleted=False))

        return count

    def get_count_students(self):
        oldSchoolYear = SchoolYear.objects(isDeleted=False, status="2").only(
            'nStudents', 'createdAt').order_by('-createdAt').first()
        if oldSchoolYear and oldSchoolYear.nStudents:
            return oldSchoolYear.nStudents
        else:
            schoolYear = SchoolYear.objects(
                isDeleted=False, status="1").only('nStudents').first()
            if schoolYear and schoolYear.nStudents:
                return schoolYear.nStudents
            else:
                return 0

    def get_diagnostics_last_five_years(self):

        periods = SchoolYear.objects(isDeleted=False).order_by('createdAt')[:5]
        data = {
            'wordsPerMinIndex': [],
            'multiplicationsPerMinIndex': [],
            'operationsPerMinIndex': []
        }
        for period in periods:
            for diag in data.keys():
                for lapse in [1, 2, 3]:

                    data[diag].append(
                        {
                            'label': period.name,
                            'serie': 'Lapso {}'.format(lapse),
                            'value': period.diagnostics['lapse{}'.format(
                                lapse)][diag]
                        }
                    )
        return data
