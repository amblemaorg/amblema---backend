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

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        from app.schemas.peca_activities_schema import ActivityFieldsSchema
        from app.schemas.peca_initial_workshop_schema import InitialWorkshopPecaSchema
        from app.schemas.special_activity_schema import SpecialActivitySchema
        from app.models.project_model import Project
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
                        document.detail['stepVideo'] = step.video
                        document.detail['stepChecklist'] = step.checklist
                        break

        # before update
        if document.id is not None:
            oldDocument = document.__class__.objects(id=document.id).first()
            if document.status != oldDocument.status:
                # activities
                if document.type == "3":
                    fields = ['date', 'uploadedFile', 'checklist']
                    peca = PecaProject.objects(
                        id=document.detail['pecaId']).first()
                    for activity in peca['lapse{}'.format(document.detail['lapse'])]['activities']:
                        if str(activity.id) == document.detail['id']:
                            for history in activity.approvalHistory:
                                if str(history.id) == str(document.id):
                                    history.status = document.status
                                    # approved
                                    if history.status == "2":
                                        # approved
                                        activity.status = "3"
                                        schema = ActivityFieldsSchema(
                                            partial=True)
                                        data = {}
                                        for field in fields:
                                            if history['detail'][field]:
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
                # testimonials
                if document.type == "2":
                    school = SchoolUser.objects(
                        id=str(document.project.school['id'])).first()
                    for testimonial in school.teachersTestimonials:
                        if str(testimonial.id) == document.detail['id']:
                            testimonial.approvalStatus = document.status
                            break
                    school.save()

                # slider
                if document.type == "4":
                    school = SchoolUser.objects(
                        id=document.detail['schoolId']).first()
                    for slider in school.slider:
                        if str(slider.id) == document.detail['id']:
                            slider.approvalStatus = document.status
                            slider.approvalHistory['status'] = document.status
                            break
                    school.save()

                # initial workshop
                if document.type == "5":
                    peca = PecaProject.objects(
                        id=document.detail['pecaId']).first()
                    initialWorkshop = peca['lapse{}'.format(
                        document.detail['lapse'])].initialWorkshop
                    for history in initialWorkshop.approvalHistory:
                        if history.id == str(document.id):
                            history.status = document.status
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
                if document.type == "6":
                    peca = PecaProject.objects(
                        id=document.detail['pecaId']).first()
                    specialActivity = peca['lapse{}'.format(
                        document.detail['lapse'])].specialActivity
                    for history in specialActivity.approvalHistory:
                        if history.id == str(document.id):
                            history.status = document.status
                            specialActivity.isInApproval = False
                            if document.status == '2':  # approved
                                schema = SpecialActivitySchema(partial=True)
                                data = schema.load(document.detail)
                                for field in schema.dump(data).keys():
                                    specialActivity[field] = data[field]
                            break
                    peca.save()

    @classmethod
    def post_save(cls, sender, document, **kwargs):
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
                            if document.detail['stepHasDate']:
                                step.date = document.detail['stepDate']
                            if document.detail['stepHasUpload']:
                                step.uploadedFile = Link(
                                    name=document.detail['stepUploadedFile']['name'],
                                    url=document.detail['stepUploadedFile']['url'])
                            if document.detail['stepHasVideo']:
                                step.video = document.detail['stepVideo']
                            if document.detail['stepHasChecklist']:
                                document.detail['checklist'] = document.detail['stepChecklist']
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


signals.pre_save.connect(RequestContentApproval.pre_save,
                         sender=RequestContentApproval)

signals.post_save.connect(RequestContentApproval.post_save,
                          sender=RequestContentApproval)
