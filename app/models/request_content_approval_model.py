# app/models/request_content_approval_model.py


from datetime import datetime

from app.models.peca_project_model import PecaProject
from app.models.shared_embedded_documents import ProjectReference
from app.models.project_model import Project, Approval, CheckElement
from app.models.school_user_model import SchoolUser

from flask import current_app
from mongoengine import (
    Document,
    EmbeddedDocument,
    fields,
    signals,
    ValidationError)


class RequestContentApproval(Document):
    code = fields.SequenceField(required=True, value_decorator=str)
    project = fields.EmbeddedDocumentField(ProjectReference)
    type = fields.StringField()
    user = fields.ReferenceField('User')
    comments = fields.StringField()
    status = fields.StringField(required=True, max_length=1, default="1")
    detail = fields.DictField()
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    isDeleted = fields.BooleanField(default=False)
    meta = {'collection': 'requests_content_approval'}

    def clean(self):
        if not current_app.config.get("TESTING"):
            self.updatedAt = datetime.utcnow()

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        from app.schemas.peca_activities_schema import ActivityFieldsSchema
        from app.schemas.peca_initial_workshop_schema import InitialWorkshopPecaSchema
        from app.schemas.peca_lapse_planning_schema import LapsePlanningPecaSchema
        from app.schemas.peca_special_lapse_activity_schema import SpecialActivitySchema
        from app.schemas.peca_yearbook_schema import YearbookSchema
        from app.schemas.peca_activity_yearbook_schema import ActivityYearbookSchema
        from app.schemas.peca_school_schema import SchoolSchema
        from app.schemas.shared_schemas import CheckSchema
        from app.models.school_user_model import SchoolUser
        from app.models.sponsor_user_model import SponsorUser
        from app.models.coordinator_user_model import CoordinatorUser
        from app.models.project_model import Project
        from app.schemas.teacher_testimonial_schema import TeacherTestimonialSchema
        from app.schemas.peca_activities_slider_schema import ActivitiesSliderSchema

        # before create
        if not document.id:
            # steps
            if document.type == "1":
                project = Project.objects(id=document.project.id).first()
                for step in project.stepsProgress.steps:
                    if step.id == document.detail['stepId']:
                        document.detail['stepName'] = step.name
                        document.detail['stepDevName'] = step.devName
                        document.detail['stepTag'] = step.tag
                        document.detail['stepIsStandard'] = step.isStandard
                        document.detail['stepHasText'] = step.hasText
                        document.detail['stepHasDate'] = step.hasDate
                        document.detail['stepHasFile'] = step.hasFile
                        document.detail['stepHasVideo'] = step.hasVideo
                        document.detail['stepHasChecklist'] = step.hasChecklist
                        document.detail['stepHasUpload'] = step.hasUpload
                        document.detail['stepText'] = step.text
                        document.detail['stepFile'] = None if not step.hasFile else {
                            "name": step.file.name,
                            "url": step.file.url
                        }
                        document.detail['stepVideo'] = None if not step.hasVideo else {
                            "name": step.video.name,
                            "url": step.video.url
                        }
                        document.detail['stepChecklist'] = None if not step.checklist else CheckSchema().dump(step.checklist, many=True)
                        break

        # before update
        if document.id is not None:
            oldDocument = document.__class__.objects(id=document.id).first()
            if document.status != oldDocument.status:
                # testimonials
                if document.type == "2":
                    school = SchoolUser.objects(
                        id=str(document.project.school['id'])).first()
                    teachersTestimonials = school.teachersTestimonials
                    for history in teachersTestimonials.approvalHistory:
                        if history.id == str(document.id):
                            history.status = document.status
                            history.comments = document.comments
                            teachersTestimonials.isInApproval = False
                            if document.status == '2':  # approved
                                schema = TeacherTestimonialSchema(partial=True)
                                data = schema.load(document.detail)
                                for field in data.keys():
                                    teachersTestimonials[field] = data[field]
                            school.save()
                            break
                # activities
                elif document.type == "3":
                    fields = ['date', 'uploadedFile', 'checklist']
                    peca = PecaProject.objects(
                        id=document.detail['pecaId']).first()
                    for activity in peca['lapse{}'.format(document.detail['lapse'])]['activities']:
                        if str(activity.id) == document.detail['id']:
                            for history in activity.approvalHistory:
                                if str(history.id) == str(document.id):
                                    history.status = document.status
                                    history.comments = document.comments
                                    # approved
                                    if history.status == "2":
                                        # approved
                                        activity.status = "3"
                                        schema = ActivityFieldsSchema(
                                            partial=True)
                                        data = {}
                                        for field in fields:
                                            if field in history['detail'] and history['detail'][field]:
                                                data[field] = history['detail'][field]
                                        data = schema.load(data)
                                        for field in data.keys():
                                            activity[field] = data[field]
                                    # rejected, cancelled
                                    elif history.status in ('3', '4'):
                                        activity.status = "1"  # pending
                                    break
                            break
                    peca.save()
                # school
                elif document.type == "4":
                    peca = PecaProject.objects(
                        id=document.detail['pecaId']).first()
                    for history in peca.school.approvalHistory:
                        if history.id == str(document.id):
                            history.status = document.status
                            history.comments = document.comments
                            peca.school.isInApproval = False
                            if history.status == '2':  # approved
                                school = SchoolUser.objects(
                                    id=peca.project.school.id).first()
                                schema = SchoolSchema(partial=True, only=(
                                    'principalFirstName',
                                    'principalLastName',
                                    'principalPhone',
                                    'principalEmail',
                                    'subPrincipalFirstName',
                                    'subPrincipalLastName',
                                    'subPrincipalEmail',
                                    'subPrincipalPhone',
                                    'facebook',
                                    'instagram',
                                    'twitter',
                                    'slider'))
                                data = schema.load(document.detail)
                                for field in data.keys():
                                    peca.school[field] = data[field]
                                    school[field] = data[field]
                                school.save()
                                break
                    peca.save()
                # initial workshop
                elif document.type == "5":
                    peca = PecaProject.objects(
                        id=document.detail['pecaId']).first()
                    initialWorkshop = peca['lapse{}'.format(
                        document.detail['lapse'])].initialWorkshop
                    for history in initialWorkshop.approvalHistory:
                        if history.id == str(document.id):
                            history.status = document.status
                            history.comments = document.comments
                            initialWorkshop.isInApproval = False
                            if document.status == "2":  # approved
                                schema = InitialWorkshopPecaSchema(
                                    partial=True)
                                data = schema.load(document.detail)
                                for field in schema.dump(data).keys():
                                    initialWorkshop[field] = data[field]
                            peca['lapse{}'.format(
                                document.detail['lapse'])].initialWorkshop = initialWorkshop
                            peca.save()
                            break
                # specialActivity
                elif document.type == "6":
                    peca = PecaProject.objects(
                        id=document.detail['pecaId']).first()
                    specialActivity = peca['lapse{}'.format(
                        document.detail['lapse'])].specialActivity
                    for history in specialActivity.approvalHistory:
                        if history.id == str(document.id):
                            history.status = document.status
                            history.comments = document.comments
                            specialActivity.isInApproval = False
                            if document.status == '2':  # approved
                                schema = SpecialActivitySchema(partial=True)
                                data = schema.load(document.detail)
                                for field in data.keys():
                                    specialActivity[field] = data[field]
                            break
                    peca.save()
                # yearbook
                elif document.type == "7":
                    peca = PecaProject.objects(
                        id=document.detail['pecaId']).first()

                    if document.status == "2":  # approved
                        school = SchoolUser.objects(
                            id=peca.project.school.id).first()
                        sponsor = SponsorUser.objects(
                            id=peca.project.sponsor.id).first()
                        coordinator = CoordinatorUser.objects(
                            id=peca.project.coordinator.id).first()

                        schema = YearbookSchema(
                            partial=True)
                        data = schema.load(document.detail)
                        for field in schema.dump(data).keys():
                            if field != 'sections':
                                peca.yearbook[field] = data[field]
                        if "sections" in data:
                            for section in data['sections']:
                                for oldSection in peca.school.sections.filter(isDeleted=False):
                                    if str(oldSection.id) == section['id']:
                                        oldSection['image'] = section['image']
                        if school.yearbook != peca.yearbook.school or school.historicalReview != peca.yearbook.historicalReview:
                            if school.yearbook != peca.yearbook.school:
                                school.yearbook = peca.yearbook.school
                                school.image = peca.yearbook.school.image
                            if school.historicalReview != peca.yearbook.historicalReview:
                                school.historicalReview = peca.yearbook.historicalReview
                            school.save()
                        if sponsor.yearbook != peca.yearbook.sponsor:
                            sponsor.yearbook = peca.yearbook.sponsor
                            sponsor.image = peca.yearbook.sponsor.image
                            sponsor.save()
                        if coordinator.yearbook != peca.yearbook.coordinator:
                            coordinator.yearbook = peca.yearbook.coordinator
                            coordinator.image = peca.yearbook.coordinator.image
                            coordinator.save()

                        for lapse in [1, 2, 3]:
                            for activity in document.detail['lapse{}'.format(lapse)]['activities']:
                                found = False
                                yearActivity = ActivityYearbookSchema().load(activity)
                                if activity['id'] == 'initialWorkshop':
                                    peca['lapse{}'.format(
                                        lapse)].initialWorkshop.yearbook = yearActivity
                                    found = True
                                elif activity['id'] == 'ambleCoins':
                                    peca['lapse{}'.format(
                                        lapse)].ambleCoins.yearbook = yearActivity
                                    found = True
                                elif activity['id'] == 'lapsePlanning':
                                    peca['lapse{}'.format(
                                        lapse)].lapsePlanning.yearbook = yearActivity
                                    found = True
                                elif activity['id'] == 'annualConvention':
                                    peca['lapse{}'.format(
                                        lapse)].annualConvention.yearbook = yearActivity
                                    found = True
                                elif activity['id'] == 'olympics':
                                    peca['lapse{}'.format(
                                        lapse)].olympics.yearbook = yearActivity
                                    found = True
                                elif activity['id'] == 'specialActivity':
                                    peca['lapse{}'.format(
                                        lapse)].specialActivity.yearbook = yearActivity
                                    found = True
                                elif activity['id'] == 'specialActivity':
                                    peca['lapse{}'.format(
                                        lapse)].specialActivity.yearbook = yearActivity
                                    found = True
                                if not found:
                                    for pecaAct in peca['lapse{}'.format(lapse)].activities:
                                        if activity['id'] == pecaAct.id:
                                            pecaAct.yearbook = yearActivity

                        for history in peca.yearbook.approvalHistory:
                            if history.id == str(document.id):
                                history.status = document.status
                        peca.yearbook.isInApproval = False
                        peca.save()
                    elif document.status in ('3', '4'):  # rejected or cancelled
                        peca.yearbook.isInApproval = False
                        for history in peca.yearbook.approvalHistory:
                            if history.id == str(document.id):
                                history.status = document.status
                                history.comments = document.comments
                        peca.save()
                 # lapse planning
                elif document.type == "8":
                    peca = PecaProject.objects(
                        id=document.detail['pecaId']).first()
                    lapsePlanning = peca['lapse{}'.format(
                        document.detail['lapse'])].lapsePlanning
                    for history in lapsePlanning.approvalHistory:
                        if history.id == str(document.id):
                            history.status = document.status
                            history.comments = document.comments
                            lapsePlanning.isInApproval = False
                            if document.status == "2":  # approved
                                schema = LapsePlanningPecaSchema(
                                    partial=True)
                                data = schema.load(document.detail)
                                for field in schema.dump(data).keys():
                                    lapsePlanning[field] = data[field]
                            peca.save()
                            break
                # activities slider
                elif document.type == '9':
                    peca = PecaProject.objects(
                        id=document.detail['pecaId']).first()
                    activitiesSlider = peca.school.activitiesSlider
                    for history in activitiesSlider.approvalHistory:
                        if history.id == str(document.id):
                            history.status = document.status
                            history.comments = document.comments
                            activitiesSlider.isInApproval = False
                            if document.status == '2':  # approved
                                schema = ActivitiesSliderSchema()
                                data = schema.load(document.detail)
                                for field in data.keys():
                                    activitiesSlider[field] = data[field]
                                SchoolUser.objects(id=peca.project.school.id).update(
                                    activitiesSlider=activitiesSlider.slider)
                            peca.save()
                            break

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        from app.schemas.shared_schemas import CheckSchema
        reciprocalFields = {
            "sponsorAgreementSchool": "schoolAgreementSponsor",
            "schoolAgreementSponsor": "sponsorAgreementSchool",
            "sponsorAgreementSchoolFoundation": "schoolAgreementFoundation",
            "schoolAgreementFoundation": "sponsorAgreementSchoolFoundation"
        }
        
        # after create
        if 'created' in kwargs and kwargs['created']:
            # steps
            if document.type == "1":
                from app.models.project_model import Project

                project = Project.objects(id=document.project.id).first()
                for step in project.stepsProgress.steps:
                    if step.id == document.detail['stepId']:
                        step.status = "2"  # in approval
                        step.approvalHistory.append(
                            Approval(
                                id=str(document.id),
                                user=str(document.user.id),
                                comments=document.comments,
                                data=document.detail,
                                status="1"
                            ))
                        if step.devName in reciprocalFields:
                            for reciprocalStep in project.stepsProgress.steps:
                                if reciprocalStep.devName == reciprocalFields[step.devName]:
                                    reciprocalStep.status = "2"  # in approval
                                    reciprocalStep.approvalHistory.append(
                                        Approval(
                                            id=str(document.id),
                                            user=str(document.user.id),
                                            comments=document.comments,
                                            data=document.detail,
                                            status="1"
                                        ))
                                    break
                        project.save()
                        break
        # after update
        else:
            # steps
            if document.type == "1":
                from app.models.project_model import Project, Link
                from app.schemas.project_schema import StepFieldsSchema

                project = Project.objects(id=document.project.id).first()

                # is approved?
                if document.status == "2":
                    for step in project.stepsProgress.steps:
                        if step.id == document.detail['stepId']:
                            if document.detail['stepHasDate'] and document.detail['stepDate']:
                                step.date = datetime.strptime(document.detail['stepDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
                            if document.detail['stepHasUpload']:
                                step.uploadedFile = Link(
                                    name=document.detail['stepUploadedFile']['name'],
                                    url=document.detail['stepUploadedFile']['url'])
                            if document.detail['stepHasVideo'] and document.detail['stepVideo']:
                                step.video = Link(
                                    name=document.detail['stepVideo']['name'],
                                    url=document.detail['stepVideo']['url'])
                            if document.detail['stepHasChecklist'] and document.detail['stepChecklist']:
                                step.checklist = [CheckSchema().load(check) for check in document.detail['stepChecklist']]
                            step.status = "3"  # approved
                            for approval in step.approvalHistory:
                                if approval.id == str(document.id):
                                    approval.status = "2"  # approved
                                    approval.updatedAt = datetime.utcnow()
                                    break

                            if document.detail['stepDevName'] in reciprocalFields:
                                for reciprocalStep in project.stepsProgress.steps:
                                    if reciprocalStep.devName == reciprocalFields[document.detail['stepDevName']]:
                                        reciprocalStep.uploadedFile = Link(
                                            name=document.detail['stepUploadedFile']['name'],
                                            url=document.detail['stepUploadedFile']['url'])
                                        reciprocalStep.approve()
                                        for reciprocalApproval in reciprocalStep.approvalHistory:
                                            if reciprocalApproval.id == str(document.id):
                                                reciprocalApproval.status = "2"  # approved
                                                reciprocalApproval.updatedAt = datetime.utcnow()
                                                break
                                        break

                            if document.detail['stepDevName'] == "coordinatorSendCurriculum":
                                project.coordinator.curriculum = step.uploadedFile
                                project.coordinator.save()
                            project.stepsProgress.updateProgress()
                            project.checkWaitingAmblemaConfirmation()
                            project.save()
                            break
                else:
                    # isn't approved?
                    for step in project.stepsProgress.steps:
                        if step.id == document.detail['stepId']:
                            step.status = "1"  # pending
                            for approval in step.approvalHistory:
                                if approval.id == str(document.id):
                                    approval.status = document.status
                                    approval.comments = document.comments
                                    approval.updatedAt = datetime.utcnow()
                                    break
                            if step.devName in reciprocalFields:
                                for reciprocalStep in project.stepsProgress.steps:
                                    if reciprocalStep.devName == reciprocalFields[document.detail['stepDevName']]:
                                        reciprocalStep.status = "1"  # pending
                                        for reciprocalApproval in reciprocalStep.approvalHistory:
                                            if reciprocalApproval.id == str(document.id):
                                                reciprocalApproval.status = document.status
                                                reciprocalApproval.comments = document.comments
                                                reciprocalApproval.updatedAt = datetime.utcnow()
                                                break
                                        break
                            project.save()
                            break

            # testimonials
            elif document.type == "2":
                if document.isDeleted:
                    school = SchoolUser.objects(
                        id=str(document.project.school['id'])).first()
                    teachersTestimonials = school.teachersTestimonials
                    for history in teachersTestimonials.approvalHistory:
                        if history.id == str(document.id):
                            history.status = "4"
                            teachersTestimonials.isInApproval = False
                            school.save()
                            break
            #activity
            elif document.type == "3":
                if document.isDeleted:
                    fields = ['date', 'uploadedFile', 'checklist']
                    peca = PecaProject.objects(
                        id=document.detail['pecaId']).first()
                    for activity in peca['lapse{}'.format(document.detail['lapse'])]['activities']:
                        if str(activity.id) == document.detail['id']:
                            for history in activity.approvalHistory:
                                if str(history.id) == str(document.id):
                                    history.status = "4"
                                    break
                            activity.status = "1"
                                        
                    peca.save()
            #school
            elif document.type == "4":
                if document.isDeleted:
                    peca = PecaProject.objects(
                        id=document.detail['pecaId']).first()
                    for history in peca.school.approvalHistory:
                        if history.id == str(document.id):
                            history.status = "4"
                            history.comments = document.comments
                            peca.school.isInApproval = False
                    peca.save()
                # initial workshop
                        
            # initial workshop
            elif document.type == "5":
                from app.schemas.peca_initial_workshop_schema import InitialWorkshopPecaSchema
                if document.isDeleted:
                    peca = PecaProject.objects(
                        id=document.detail['pecaId']).first()
                    initialWorkshop = peca['lapse{}'.format(
                        document.detail['lapse'])].initialWorkshop
                    for history in initialWorkshop.approvalHistory:
                        if history.id == str(document.id):
                            history.status = "4"
                            initialWorkshop.isInApproval = False
                            peca['lapse{}'.format(
                                document.detail['lapse'])].initialWorkshop = initialWorkshop
                            peca.save()
                            break
            # specialActivity
            elif document.type == "6":
                if document.isDeleted:
                    peca = PecaProject.objects(
                        id=document.detail['pecaId']).first()
                    specialActivity = peca['lapse{}'.format(
                        document.detail['lapse'])].specialActivity
                    for history in specialActivity.approvalHistory:
                        if history.id == str(document.id):
                            history.status = "4"
                            specialActivity.isInApproval = False
                            peca.save()
                            break
            #yearbook
            elif document.type == "7":
                if document.isDeleted:
                    peca = PecaProject.objects(
                        id=document.detail['pecaId']).first()

                    peca.yearbook.isInApproval = False
                    for history in peca.yearbook.approvalHistory:
                        if history.id == str(document.id):
                            history.status = document.status
                            peca.save()
                            break
            #lapsePlanning                
            elif document.type == "8":
                from app.schemas.peca_lapse_planning_schema import LapsePlanningPecaSchema
                if document.isDeleted:
                    peca = PecaProject.objects(
                        id=document.detail['pecaId']).first()
                    lapsePlanning = peca['lapse{}'.format(
                        document.detail['lapse'])].lapsePlanning
                    for history in lapsePlanning.approvalHistory:
                        if history.id == str(document.id):
                            history.status = "4"
                            lapsePlanning.isInApproval = False
                            peca.save()
                            break
            # activities slider
            elif document.type == '9':
                if document.isDeleted:
                    peca = PecaProject.objects(
                        id=document.detail['pecaId']).first()
                    activitiesSlider = peca.school.activitiesSlider
                    for history in activitiesSlider.approvalHistory:
                        if history.id == str(document.id):
                            history.status = "4"
                            history.comments = document.comments
                            activitiesSlider.isInApproval = False
                            peca.save()
                            break
                                    
signals.pre_save.connect(RequestContentApproval.pre_save,
                         sender=RequestContentApproval)

signals.post_save.connect(RequestContentApproval.post_save,
                          sender=RequestContentApproval)
