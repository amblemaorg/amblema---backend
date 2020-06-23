# app/services/peca_project_service.py


from functools import reduce
import operator

from flask import current_app
from marshmallow import ValidationError
from mongoengine import Q

from app.models.school_year_model import SchoolYear
from app.models.peca_project_model import PecaProject
from app.schemas.peca_project_schema import PecaProjectSchema, SchoolSchema
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields
from app.helpers.error_helpers import RegisterNotFound


class PecaProjectService():

    def getAll(self, filters=None):
        if filters:
            filterList = []
            for f in filters:
                if f['field'] == 'school':
                    filterList.append(Q(**{'project__school': f['value']}))
                else:
                    filterList.append(Q(**{f['field']: f['value']}))

            records = PecaProject.objects(isDeleted=False).filter(
                reduce(operator.and_, filterList)).exclude('school')
        else:
            records = PecaProject.objects(isDeleted=False).exclude('school')

        schema = PecaProjectSchema(exclude=('school',))
        return {"records": schema.dump(records, many=True)}, 200

    def get(self, id):
        from app.models.school_user_model import SchoolUser
        from app.models.sponsor_user_model import SponsorUser
        from app.models.coordinator_user_model import CoordinatorUser
        from app.schemas.school_user_schema import TeacherTestimonialSchema
        from app.schemas.teacher_schema import TeacherSchema
        from app.schemas.shared_schemas import ImageStatusSchema
        from app.schemas.peca_yearbook_schema import YearbookSchema

        peca = PecaProject.objects(
            isDeleted=False, id=id).first()
        if peca:
            schema = PecaProjectSchema()
            data = schema.dump(peca)
            school = SchoolUser.objects(
                id=peca.project.school.id).first()
            data['school']['teachers'] = TeacherSchema().dump(
                school.teachers, many=True)
            data['school']['slider'] = ImageStatusSchema().dump(
                school.slider, many=True)
            data['school']['teachersTestimonials'] = TeacherTestimonialSchema().dump(
                school.teachersTestimonials, many=True
            )
            sponsor = SponsorUser.objects.get(id=peca.project.sponsor.id)
            coordinator = CoordinatorUser.objects.get(
                id=peca.project.coordinator.id)

            if not peca.yearbook.historicalReview.image:
                data['yearbook']['historicalReview']['content'] = school.historicalReview.content
                data['yearbook']['historicalReview']['image'] = school.historicalReview.image
            if not peca.yearbook.school.image:
                data['yearbook']['school']['name'] = school.name
                data['yearbook']['school']['image'] = school.image
                data['yearbook']['school']['content'] = school.yearbook.content
            if not peca.yearbook.sponsor.image:
                data['yearbook']['sponsor']['name'] = sponsor.name
                data['yearbook']['sponsor']['image'] = sponsor.image
                data['yearbook']['sponsor']['content'] = sponsor.yearbook.content
            if not peca.yearbook.coordinator.image:
                data['yearbook']['coordinator']['name'] = coordinator.name
                data['yearbook']['coordinator']['image'] = coordinator.image
                data['yearbook']['coordinator']['content'] = coordinator.yearbook.content

            data['yearbook']['lapse1'] = {
                'diagnosticSummary': [],
                'activities': []
            }
            data['yearbook']['lapse2'] = {
                'diagnosticSummary': [],
                'activities': []
            }
            data['yearbook']['lapse3'] = {
                'diagnosticSummary': [],
                'activities': []
            }

            for section in sorted(
                    peca.school.sections.filter(isDeleted=False), key=lambda x: (x['grade'], x['name'])):

                summary = section.diagnostics
                for i in range(1, 4):
                    data['yearbook']['lapse{}'.format(i)]['diagnosticSummary'].append(
                        {
                            'grade': section.grade,
                            'name': section.name,
                            'wordsPerMin': summary['lapse{}'.format(i)]['wordsPerMin'],
                            'wordsPerMinIndex': summary['lapse{}'.format(i)]['wordsPerMinIndex'],
                            'multiplicationsPerMin': summary['lapse{}'.format(i)]['multiplicationsPerMin'],
                            'multiplicationsPerMinIndex': summary['lapse{}'.format(i)]['multiplicationsPerMinIndex'],
                            'operationsPerMin': summary['lapse{}'.format(i)]['operationsPerMin'],
                            'operationsPerMinIndex': summary['lapse{}'.format(i)]['operationsPerMinIndex']
                        }
                    )
            for i in range(1, 4):
                lapse = peca['lapse{}'.format(i)]
                lapseData = data['yearbook']['lapse{}'.format(i)]

                if lapse.initialWorkshop:
                    lapseData['activities'].append(
                        {
                            'id': 'initialWorkshop',
                            'name': 'Taller inicial',
                            'description': lapse.initialWorkshop.yearbook.description,
                            'images': lapse.initialWorkshop.yearbook.images
                        }
                    )

                if lapse.ambleCoins:
                    lapseData['activities'].append(
                        {
                            'id': 'ambleCoins',
                            'name': 'AmbLeMonedas',
                            'description': lapse.ambleCoins.yearbook.description,
                            'images': lapse.ambleCoins.yearbook.images
                        }
                    )
                if lapse.lapsePlanning:
                    lapseData['activities'].append(
                        {
                            'id': 'lapsePlanning',
                            'name': 'Planificación de lapso',
                            'description': lapse.lapsePlanning.yearbook.description,
                            'images': lapse.lapsePlanning.yearbook.images
                        }
                    )
                if lapse.annualConvention:
                    lapseData['activities'].append(
                        {
                            'id': 'annualConvention',
                            'name': 'Convención anual',
                            'description': lapse.annualConvention.yearbook.description,
                            'images': lapse.annualConvention.yearbook.images
                        }
                    )
                if lapse.olympics:
                    lapseData['activities'].append(
                        {
                            'id': 'olympics',
                            'name': 'Olimpiadas matemáticas',
                            'description': lapse.olympics.yearbook.description,
                            'images': lapse.olympics.yearbook.images
                        }
                    )
                if lapse.specialActivity:
                    lapseData['activities'].append(
                        {
                            'id': 'specialActivity',
                            'name': 'Actividad especial de lapso {}'.format(i),
                            'description': lapse.specialActivity.yearbook.description,
                            'images': lapse.specialActivity.yearbook.images
                        }
                    )
                for activity in lapse.activities:
                    lapseData['activities'].append(
                        {
                            'id': str(activity.id),
                            'name': activity.name,
                            'description': activity.yearbook.description,
                            'images': activity.yearbook.images
                        }
                    )
            return data, 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": id})

    def updateSchool(self, id, jsonData):
        pecaProject = PecaProject.objects(
            isDeleted=False, id=id).first()
        if pecaProject:
            try:
                schema = SchoolSchema(partial=True)
                data = schema.load(jsonData)
                for field in schema.dump(data).keys():
                    pecaProject.school[field] = data[field]
                try:
                    pecaProject.save()
                    return schema.dump(pecaProject.school), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": id})

    def getSchool(self, id):
        pecaProject = PecaProject.objects(
            isDeleted=False, id=id).first()
        if pecaProject:
            try:
                schema = SchoolSchema()
                return schema.dump(pecaProject.school), 200
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": id})

    def initPecaSetting(self, peca):
        from app.models.school_year_model import SchoolYear
        from app.models.peca_amblecoins_model import AmblecoinsPeca, AmbleSection
        from app.models.peca_olympics_model import Olympics
        from app.models.peca_project_model import Lapse
        from app.models.peca_annual_preparation_model import AnnualPreparationPeca
        from app.models.peca_annual_convention_model import AnnualConventionPeca, CheckElement
        from app.models.peca_activities_model import ActivityPeca

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only('pecaSetting').first()

        for i in range(1, 4):
            peca['lapse{}'.format(i)] = Lapse()
            pecaSettingLapse = schoolYear.pecaSetting['lapse{}'.format(i)]

            if pecaSettingLapse.ambleCoins.status == "1":
                peca['lapse{}'.format(i)].ambleCoins = AmblecoinsPeca()
            else:
                peca['lapse{}'.format(i)].ambleCoins = None

            if pecaSettingLapse.mathOlympic.status == "1":
                peca['lapse{}'.format(i)].olympics = Olympics()
            else:
                peca['lapse{}'.format(i)].olympics = None

            if pecaSettingLapse.annualPreparation.status == "1":
                peca['lapse{}'.format(i)].annualPreparation = AnnualPreparationPeca(
                    step1Description=pecaSettingLapse.annualPreparation.step1Description,
                    step2Description=pecaSettingLapse.annualPreparation.step2Description,
                    step3Description=pecaSettingLapse.annualPreparation.step3Description,
                    step4Description=pecaSettingLapse.annualPreparation.step4Description
                )
            else:
                peca['lapse{}'.format(i)].annualPreparation = None

            if pecaSettingLapse.annualConvention.status == "1":
                annualConvention = AnnualConventionPeca()
                for element in pecaSettingLapse.annualConvention.checklist:
                    annualConvention.checklist.append(
                        CheckElement(
                            id=str(element.id),
                            name=element.name,
                            checked=False
                        ))
                peca['lapse{}'.format(i)].annualConvention = annualConvention
            else:
                peca['lapse{}'.format(i)].annualConvention = None

            for activity in pecaSettingLapse.activities:
                if activity.status == "1":
                    peca['lapse{}'.format(i)].activities.append(
                        ActivityPeca(
                            id=str(activity.id),
                            name=activity.name,
                            devName=activity.devName,
                            hasText=activity.hasText,
                            hasDate=activity.hasDate,
                            hasFile=activity.hasFile,
                            hasVideo=activity.hasVideo,
                            hasChecklist=activity.hasChecklist,
                            hasUpload=activity.hasUpload,
                            text=activity.text,
                            file=activity.file,
                            video=activity.video,
                            checklist=None if not activity.hasChecklist else [CheckElement(
                                id=chk.id, name=chk.name) for chk in activity.checklist],
                            approvalType=activity.approvalType,
                            isStandard=activity.isStandard,
                            status=activity.status,
                            createdAt=activity.createdAt,
                            updatedAt=activity.updatedAt
                        )
                    )
