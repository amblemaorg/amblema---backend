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
from app.helpers.ma_schema_fields import serialize_links


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
        from app.schemas.monitoring_activity_schema import MonitoringActivitySchema
        from app.schemas.environmental_project_schema import EnvironmentalProjectSchema
        from app.models.project_model import Project

        peca = PecaProject.objects(
            isDeleted=False, id=id).first()
        if peca:
            schema = PecaProjectSchema()
            schoolYear = peca.schoolYear.fetch()
            project = Project.objects(id=peca.project.id, isDeleted=False).only(
                'stepsProgress').first()
            amblemaConfirmation = project.stepsProgress.steps.filter(
                devName='amblemaConfirmation', tag='1').first()
            peca.school.sections = peca.school.sections.filter(isDeleted=False)
            for section in peca.school.sections:
                section.students = section.students.filter(isDeleted=False)
            data = schema.dump(peca)
            # field for see go to steps option in peca menu
            data['steps'] = str(
                project.id) if amblemaConfirmation and amblemaConfirmation.status == "3" else False
            data['monitoringActivities'] = MonitoringActivitySchema().dump(
                schoolYear.pecaSetting.monitoringActivities)
            school = SchoolUser.objects(
                id=peca.project.school.id).first()
            data['school']['teachers'] = TeacherSchema().dump(
                school.teachers.filter(isDeleted=False), many=True)
            data['school']['slider'] = ImageStatusSchema().dump(
                school.slider, many=True)
            data['school']['teachersTestimonials'] = TeacherTestimonialSchema().dump(
                school.teachersTestimonials
            )
            sponsor = SponsorUser.objects.get(id=peca.project.sponsor.id)
            coordinator = CoordinatorUser.objects.get(
                id=peca.project.coordinator.id)

            data['yearbook'] = self.getYearbookData(peca, school,sponsor,coordinator, data['yearbook'])
            return data, 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": id})

    def initPecaSetting(self, peca):
        from app.models.school_year_model import SchoolYear
        from app.models.peca_initial_workshop_model import InitialWorkshopPeca
        from app.models.peca_lapse_planning_model import LapsePlanningPeca
        from app.models.peca_amblecoins_model import AmblecoinsPeca, AmbleSection
        from app.models.peca_olympics_model import Olympics
        from app.models.peca_project_model import Lapse
        from app.models.peca_annual_preparation_model import AnnualPreparationPeca
        from app.models.peca_annual_convention_model import AnnualConventionPeca
        from app.models.peca_activities_model import ActivityPeca
        from app.models.peca_special_lapse_activity_model import SpecialActivityPeca
        from app.models.peca_environmental_project_model import EnvironmentalProjectPeca
        from app.schemas.peca_environmental_project_schema import EnvironmentalProjectPecaSchema
        from app.schemas.environmental_project_schema import EnvironmentalProjectSchema
        from app.models.shared_embedded_documents import CheckElement

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only('pecaSetting').first()

        for i in range(1, 4):
            peca['lapse{}'.format(i)] = Lapse()
            pecaSettingLapse = schoolYear.pecaSetting['lapse{}'.format(i)]

            if pecaSettingLapse.initialWorkshop.status == "1":
                peca['lapse{}'.format(i)].initialWorkshop = InitialWorkshopPeca()
            else:
                peca['lapse{}'.format(i)].initialWorkshop = None

            if pecaSettingLapse.ambleCoins.status == "1":
                peca['lapse{}'.format(i)].ambleCoins = AmblecoinsPeca(
                    teachersMeetingFile=pecaSettingLapse.ambleCoins.teachersMeetingFile,
                    teachersMeetingDescription=pecaSettingLapse.ambleCoins.teachersMeetingDescription,
                    piggyBankDescription=pecaSettingLapse.ambleCoins.piggyBankDescription,
                    piggyBankSlider=pecaSettingLapse.ambleCoins.piggyBankSlider
                )
            else:
                peca['lapse{}'.format(i)].ambleCoins = None
            
            if pecaSettingLapse.lapsePlanning.status == "1":
                peca['lapse{}'.format(i)].lapsePlanning = LapsePlanningPeca(
                    proposalFundationFile=pecaSettingLapse.lapsePlanning.proposalFundationFile,
                    proposalFundationDescription=pecaSettingLapse.lapsePlanning.proposalFundationDescription,
                    meetingDescription=pecaSettingLapse.lapsePlanning.meetingDescription
                )
            else:
                peca['lapse{}'.format(i)].lapsePlanning = None

            if pecaSettingLapse.mathOlympic.status == "1":
                peca['lapse{}'.format(i)].olympics = Olympics(
                    file = pecaSettingLapse.mathOlympic.file,
                    description = pecaSettingLapse.mathOlympic.description,
                    date = pecaSettingLapse.mathOlympic.date
                )
                if pecaSettingLapse.mathOlympic.date:
                    peca.scheduleActivity(
                            devName="olympics__date",
                            activityId="mathOlympic",
                            subject="Olimpíadas matemáticas",
                            startTime=pecaSettingLapse.mathOlympic.date,
                            description=pecaSettingLapse.mathOlympic.description
                        )
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

            if pecaSettingLapse.specialLapseActivity.status == "1":
                specialActivity = SpecialActivityPeca()
                peca['lapse{}'.format(i)].specialActivity = specialActivity
            else:
                peca['lapse{}'.format(i)].specialActivity = None

            for activity in pecaSettingLapse.activities.filter(isDeleted=False):
                if activity.status == "1":
                    actPeca = ActivityPeca(
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
                            approvalType=activity.approvalType,
                            isStandard=activity.isStandard,
                            status=activity.status,
                            createdAt=activity.createdAt,
                            updatedAt=activity.updatedAt
                        )
                    if activity.hasChecklist:
                        for check in activity.checklist:
                            actPeca.checklist.append(
                                CheckElement(name=check.name, id=check.id))
                    peca['lapse{}'.format(i)].activities.append(
                        actPeca
                    )
            if schoolYear.pecaSetting.environmentalProject and schoolYear.pecaSetting.environmentalProject.name:
                envProjectStg = EnvironmentalProjectSchema().dump(schoolYear.pecaSetting.environmentalProject)
                envProjectData = EnvironmentalProjectPecaSchema().load(envProjectStg)
                envProject = EnvironmentalProjectPeca()
                for field in envProjectData.keys():
                    envProject[field] = envProjectData[field]
                peca.environmentalProject = envProject

    def getYearbookData(self, peca, school, sponsor, coordinator, data):
        
        if not peca.yearbook.historicalReview.image:
            data['historicalReview']['content'] = school.historicalReview.content
            data['historicalReview']['image'] = serialize_links(
                school.historicalReview.image)
        if not peca.yearbook.school.image:
            data['school']['name'] = school.name
            data['school']['image'] = serialize_links(
                school.image)
            data['school']['content'] = school.yearbook.content
        if not peca.yearbook.sponsor.image:
            data['sponsor']['name'] = sponsor.name
            data['sponsor']['image'] = serialize_links(
                sponsor.image)
            data['sponsor']['content'] = sponsor.yearbook.content
        if not peca.yearbook.coordinator.image:
            data['coordinator']['name'] = coordinator.name
            data['coordinator']['image'] = serialize_links(
                coordinator.image)
            data['coordinator']['content'] = coordinator.yearbook.content

        data['lapse1']['diagnosticSummary'] = []
        data['lapse1']['activities'] = []
        data['lapse2']['diagnosticSummary'] = []
        data['lapse2']['activities'] = []
        data['lapse3']['diagnosticSummary'] = []
        data['lapse3']['activities'] = []

        for section in sorted(
                peca.school.sections.filter(isDeleted=False), key=lambda x: (x['grade'], x['name'])):

            summary = section.diagnostics
            for i in range(1, 4):
                data['lapse{}'.format(i)]['diagnosticSummary'].append(
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
            lapseData = data['lapse{}'.format(i)]

            if lapse.initialWorkshop:
                lapseData['activities'].append(
                    {
                        'id': 'initialWorkshop',
                        'name': 'Taller inicial',
                        'description': lapse.initialWorkshop.yearbook.description,
                        'images': serialize_links(lapse.initialWorkshop.yearbook.images)
                    }
                )

            if lapse.ambleCoins:
                lapseData['activities'].append(
                    {
                        'id': 'ambleCoins',
                        'name': 'AmbLeMonedas',
                        'description': lapse.ambleCoins.yearbook.description,
                        'images': serialize_links(lapse.ambleCoins.yearbook.images)
                    }
                )
            if lapse.lapsePlanning:
                lapseData['activities'].append(
                    {
                        'id': 'lapsePlanning',
                        'name': 'Planificación de lapso',
                        'description': lapse.lapsePlanning.yearbook.description,
                        'images': serialize_links(lapse.lapsePlanning.yearbook.images)
                    }
                )
            if lapse.annualConvention:
                lapseData['activities'].append(
                    {
                        'id': 'annualConvention',
                        'name': 'Convención anual',
                        'description': lapse.annualConvention.yearbook.description,
                        'images': serialize_links(lapse.annualConvention.yearbook.images)
                    }
                )
            if lapse.olympics:
                lapseData['activities'].append(
                    {
                        'id': 'olympics',
                        'name': 'Olimpíadas matemáticas',
                        'description': lapse.olympics.yearbook.description,
                        'images': serialize_links(lapse.olympics.yearbook.images)
                    }
                )
            if lapse.specialActivity:
                lapseData['activities'].append(
                    {
                        'id': 'specialActivity',
                        'name': 'Actividad especial de lapso {}'.format(i),
                        'description': lapse.specialActivity.yearbook.description,
                        'images': serialize_links(lapse.specialActivity.yearbook.images)
                    }
                )
            for activity in lapse.activities:
                lapseData['activities'].append(
                    {
                        'id': str(activity.id),
                        'name': activity.name,
                        'description': activity.yearbook.description,
                        'images': serialize_links(activity.yearbook.images)
                    }
                )
        return data