# app/models/request_step_approval_model.py


from datetime import datetime

from flask import current_app
from mongoengine import (
    Document,
    EmbeddedDocument,
    fields,
    signals,
    ValidationError)

from app.models.project_model import Project, Approval, CheckElement
from app.models.shared_embedded_documents import Link
from app.models.user_model import User


class RequestStepApproval(Document):
    stepId = fields.StringField(required=True)
    project = fields.ReferenceField(Project, required=True)
    user = fields.ReferenceField(User)
    comments = fields.StringField()
    status = fields.StringField(required=True, max_length=1, default="1")
    stepName = fields.StringField()
    stepDevName = fields.StringField()
    stepTag = fields.StringField()
    stepHasText = fields.BooleanField()
    stepHasDate = fields.BooleanField()
    stepHasFile = fields.BooleanField()
    stepHasVideo = fields.BooleanField()
    stepHasChecklist = fields.BooleanField()
    stepHasUpload = fields.BooleanField()
    stepText = fields.StringField()
    stepFile = fields.EmbeddedDocumentField(Link)
    stepVideo = fields.EmbeddedDocumentField(Link)
    stepChecklist = fields.EmbeddedDocumentListField(CheckElement)
    stepDate = fields.DateTimeField(null=True)
    stepUploadedFile = fields.EmbeddedDocumentField(
        Link, is_file=True, null=True, default=None)
    stepIsStandard = fields.BooleanField()
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    isDeleted = fields.BooleanField(default=False)
    meta = {'collection': 'requests_step_approval'}

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if not document.id:
            for step in document.project.stepsProgress.steps:
                if step.id == document.stepId:
                    document.stepName = step.name
                    document.stepDevName = step.devName
                    document.stepTag = step.tag
                    document.stepIsStandard = step.isStandard
                    document.stepHasText = step.hasText
                    document.stepHasDate = step.hasDate
                    document.stepHasFile = step.hasFile
                    document.stepHasVideo = step.hasVideo
                    document.stepHasChecklist = step.hasChecklist
                    document.stepHasUpload = step.hasUpload
                    document.stepText = step.text
                    document.stepFile = step.file
                    document.stepVideo = step.video
                    document.stepChecklist = step.checklist
                    break

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        reciprocalFields = {
            "sponsorAgreementSchool": "schoolAgreementSponsor",
            "schoolAgreementSponsor": "sponsorAgreementSchool",
            "sponsorAgreementSchoolFoundation": "schoolAgreementFoundation",
            "schoolAgreementFoundation": "sponsorAgreementSchoolFoundation"
        }
        if 'created' in kwargs and kwargs['created']:
            from app.schemas.request_step_approval_schema import RequestStepApprovalSchema
            for step in document.project.stepsProgress.steps:
                if step.id == document.stepId:
                    step.status = "2"  # in approval
                    step.approvalHistory.append(
                        Approval(
                            id=str(document.id),
                            user=str(document.user.id),
                            comments=document.comments,
                            data=RequestStepApprovalSchema().dump(document),
                            status="1"
                        ))
                    if step.devName in reciprocalFields:
                        for reciprocalStep in document.project.stepsProgress.steps:
                            if reciprocalStep.devName == reciprocalFields[step.devName]:
                                reciprocalStep.status = "2"  # in approval
                                reciprocalStep.approvalHistory.append(
                                    Approval(
                                        id=str(document.id),
                                        user=str(document.user.id),
                                        comments=document.comments,
                                        data=RequestStepApprovalSchema().dump(document),
                                        status="1"
                                    ))
                                break
                    document.project.save()
                    break
        else:
            # is approved?
            if document.status == "2":
                for step in document.project.stepsProgress.steps:
                    if step.id == document.stepId:
                        if document.stepHasDate:
                            step.date = document.stepDate
                        if document.stepHasUpload:
                            step.uploadedFile = document.stepUploadedFile
                        if document.stepHasVideo:
                            step.video = document.stepVideo
                        if document.stepHasChecklist:
                            document.checklist = document.stepChecklist
                        step.status = "3"  # approved
                        for approval in step.approvalHistory:
                            if approval.id == str(document.id):
                                approval.status = "2"  # approved
                                approval.updatedAt = datetime.utcnow()
                                break

                        if document.stepDevName in reciprocalFields:
                            for reciprocalStep in document.project.stepsProgress.steps:
                                if reciprocalStep.devName == reciprocalFields[document.stepDevName]:
                                    reciprocalStep.uploadedFile = document.stepUploadedFile
                                    reciprocalStep.approve()
                                    for reciprocalApproval in reciprocalStep.approvalHistory:
                                        if reciprocalApproval.id == str(document.id):
                                            reciprocalApproval.status = "2"  # approved
                                            reciprocalApproval.updatedAt = datetime.utcnow()
                                            break
                                    break

                        if document.stepDevName == "coordinatorSendCurriculum":
                            document.project.coordinator.curriculum = step.uploadedFile
                            document.project.coordinator.save()
                        document.project.stepsProgress.updateProgress()
                        document.project.checkWaitingAmblemaConfirmation()
                        document.project.save()
                        break
            else:
                # isn't approved?
                for step in document.project.stepsProgress.steps:
                    if step.id == document.stepId:
                        step.status = "1"  # pending
                        for approval in step.approvalHistory:
                            if approval.id == str(document.id):
                                approval.status = document.status
                                approval.comments = document.comments
                                approval.updatedAt = datetime.utcnow()
                                break
                        if step.devName in reciprocalFields:
                            for reciprocalStep in document.project.stepsProgress.steps:
                                if reciprocalStep.devName == reciprocalFields[document.stepDevName]:
                                    reciprocalStep.status = "1"  # pending
                                    for reciprocalApproval in reciprocalStep.approvalHistory:
                                        if reciprocalApproval.id == str(document.id):
                                            reciprocalApproval.status = document.status
                                            reciprocalApproval.comments = document.comments
                                            reciprocalApproval.updatedAt = datetime.utcnow()
                                            break
                                    break
                        document.project.save()
                        break


signals.pre_save.connect(RequestStepApproval.pre_save,
                         sender=RequestStepApproval)
signals.post_save.connect(RequestStepApproval.post_save,
                          sender=RequestStepApproval)
