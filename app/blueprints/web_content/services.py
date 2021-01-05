# app/blueprints/web_content/services.py


from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q
from flask import current_app

from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields
from app.services.generic_service import GenericServices
from app.blueprints.web_content.models.web_content import WebContent, WebContentSchema
from app.services.statistics_service import StatisticsService
from app.models.school_user_model import SchoolUser
from app.schemas.school_user_schema import SchoolUserSchema
from app.models.peca_project_model import PecaProject
from app.models.school_year_model import SchoolYear
from app.models.project_model import Project


class WebContentService(GenericServices):

    def getAllRecords(self, page, only=None, exclude=()):
        """
        get all available states records
        """
        schema = self.Schema(only=only, exclude=exclude)
        if page:
            schema = self.Schema(only=[page], exclude=exclude)
            record = self.Model.objects().only(page).first()
            data = schema.dump(record)
            if page == 'homePage':
                statisticsService = StatisticsService()
                counts = statisticsService.get_count_home_page()
                data['homePage']['nSchools'] = counts['nSchools']
                data['homePage']['nStudents'] = counts['nStudents']
                data['homePage']['nTeachers'] = counts['nTeachers']
                data['homePage']['nSponsors'] = counts['nSponsors']
                data['homePage']['nCoordinators'] = counts['nCoordinators']
                data['homePage']['diagnostics'] = statisticsService.get_diagnostics_last_five_years()
            if page == 'sponsorPage':
                data['sponsorPage']['sponsors'] = sorted(
                    data['sponsorPage']['sponsors'], key=lambda x: (x['position']))

            return data, 200

    def saveRecord(self, jsonData, only=None):
        """
        Method that saves a new record.
        params: jsonData
        """
        schema = self.Schema(only=only)
        try:
            data = schema.load(jsonData, partial=True)

            record = WebContent.objects().first()
            if not record:
                record = self.Model()

            for field in data.keys():
                record[field] = data[field]

            try:
                record.save()
                return schema.dump(record), 201
            except Exception as e:
                return {'status': 0, 'message': str(e)}, 400
        except ValidationError as err:
            return err.messages, 400


class SchoolPageContentService():

    def getAllRecords(self):
        schema = SchoolUserSchema(
            partial=True, only=('id', 'code', 'slug', 'name', 'coordinate'))
        schools = []
        currentPeriod = SchoolYear.objects(isDeleted=False, status="1").first()
        if currentPeriod:
            schoolsIds = []
            pecas = PecaProject.objects(isDeleted=False, schoolYear=currentPeriod.id)
            for peca in pecas:
                schoolsIds.append(peca.project.school.id)
            schools = SchoolUser.objects(isDeleted=False, pk__in=schoolsIds, coordinate__exists=True).all()
            schools = schema.dump(schools, many=True)
        return {"records": schools}, 200

    def get(self, id):

        currentPeriod = SchoolYear.objects(isDeleted=False, status="1").first()
        code = id.split("_", 1)[0]
        school = SchoolUser.objects(code=code, isDeleted=False).first()
        nearbySchools = SchoolUser.objects(
            code__ne=code,
            isDeleted=False, coordinate__near=school.coordinate, project__schoolYears__0__exists=True)[:3]
        pecasIds = [peca.pecaId for peca in school.project.schoolYears]
        pecas = PecaProject.objects(
            id__in=pecasIds, isDeleted=False).order_by('createdAt')[:5]
        currentPeca = pecas[len(pecas)-1]

        diagnostics = {
            'wordsPerMinIndex': [],
            'multiplicationsPerMinIndex': [],
            'operationsPerMinIndex': []
        }
        for peca in pecas:
            for diag in diagnostics.keys():
                hasInfo = False
                for lapse in [1, 2, 3]:
                    if peca.school.diagnostics['lapse{}'.format(
                                lapse)][diag]:
                        hasInfo = True
                if hasInfo:
                    for lapse in [1, 2, 3]:
                        diagnostics[diag].append(
                            {
                                'createdAt': peca.createdAt,
                                'label': peca.schoolYearName,
                                'serie': 'Lapso {}'.format(lapse),
                                'value': peca.school.diagnostics['lapse{}'.format(
                                    lapse)][diag]
                            }
                        )
        for diag in diagnostics.keys():
            diagnostics[diag] = sorted(
                diagnostics[diag], reverse=True, key=lambda x: (x['createdAt']))
        olympicsDescription = ""
        for lapse in [1, 2, 3]:
            if currentPeriod.pecaSetting['lapse{}'.format(lapse)].mathOlympic.status == "1":
                olympicsDescription = currentPeriod.pecaSetting['lapse{}'.format(
                    lapse)].mathOlympic.description

        actsId = {}
        activities = []
        nextActivities = []
        for lapse in [1, 2, 3]:
            setting = currentPeriod.pecaSetting['lapse{}'.format(lapse)]
            if setting.initialWorkshop.status == "1" and 'initialWorkshop' not in actsId:
                actsId['initialWorkshop'] = setting.initialWorkshop
                activities.append(
                    {
                        'name': setting.initialWorkshop.name,
                        'description': setting.initialWorkshop.description
                    })
            if setting.ambleCoins.status == "1" and 'ambleCoins' not in actsId:
                actsId['ambleCoins'] = setting.ambleCoins
                activities.append(
                    {
                        'name': setting.ambleCoins.name,
                        'description': setting.ambleCoins.description
                    })
            if setting.annualConvention.status == "1" and 'annualConvention' not in actsId:
                actsId['annualConvention'] = setting.annualConvention
                activities.append(
                    {
                        'name': setting.annualConvention.name,
                        'description': setting.annualConvention.description
                    })
            if setting.mathOlympic.status == "1" and 'mathOlympic' not in actsId:
                actsId['mathOlympic'] = setting.mathOlympic
                activities.append(
                    {
                        'name': setting.mathOlympic.name,
                        'description': setting.mathOlympic.webDescription
                    })
            if setting.specialLapseActivity.status == "1" and 'specialLapseActivity' not in actsId:
                actsId['specialLapseActivity'] = setting.specialLapseActivity
                activities.append(
                    {
                        'name': setting.specialLapseActivity.name,
                        'description': setting.specialLapseActivity.description
                    })
            for genericAct in setting.activities:
                if genericAct.status == "1" and str(genericAct.id) not in actsId and not genericAct.isDeleted:
                    actsId[str(genericAct.id)] = genericAct
                    activities.append(
                        {
                            'name': genericAct.name,
                            'description': genericAct.description
                        })
        if currentPeriod.pecaSetting.environmentalProject.name:
            activities.append(
                {
                    'name': currentPeriod.pecaSetting.environmentalProject.name,
                    'description': currentPeriod.pecaSetting.environmentalProject.description
                }
            )
        for act in currentPeca.schedule:
            if act.activityId in actsId:
                nextActivities.append({
                    'name': actsId[act.activityId].name,
                    'description': actsId[act.activityId].description if act.activityId != 'mathOlympic' else actsId[act.activityId].webDescription,
                    'date': act.startTime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                })

        schema = SchoolUserSchema(
            partial=True, only=(
                'id',
                'name',
                'slug',
                'slider',
                'nTeachers',
                'nAdministrativeStaff',
                'nLaborStaff',
                'olympicsSummary',
                'activitiesSlider',
                'teachersTestimonials',
                'facebook',
                'instagram',
                'twitter'))
        data = schema.dump(school)
        data['coordinator'] = school.project.coordinator.name
        data['sponsor'] = school.project.sponsor.name
        data['address'] = '{}, {}, Venezuela'.format(
            school.addressMunicipality.name, school.addressState.name)
        data['nearbySchools'] = SchoolUserSchema(
            partial=True, only=('id', 'slug', 'name', 'image')).dump(nearbySchools, many=True)
        data['nStudents'] = peca.school.nStudents
        data['diagnostics'] = diagnostics
        data['olympicsSummary']['description'] = olympicsDescription
        data['activities'] = activities
        data['nextActivities'] = nextActivities

        return data, 200
