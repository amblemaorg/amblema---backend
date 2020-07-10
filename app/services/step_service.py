# app/services/step_service.py


import re

from flask import current_app
from mongoengine import ValidationError
from app.models.school_year_model import SchoolYear
from app.helpers.error_helpers import CSTM_Exception


class StepsService():

    def handler_steps_before_create(self, document):

        # validate there is a current school year active
        year = SchoolYear.objects(status="1", isDeleted=False).first()
        if not year:
            raise ValidationError(
                message="There is not an active school year")
        document.schoolYear = year

        # replace special characters for _ and set devName field
        if not document.isStandard:
            document.devName = re.sub(
                r'[\W_]', '_', document.name.strip().lower())
        if not document.sort:
            last = document.__class__.objects(
                tag=document.tag).order_by('-sort').first()
            if last:
                document.sort = last.sort + 1
            else:
                document.sort = 1

    def handler_steps_before_upd(self, document, oldDocument):
        from app.models.project_model import Project, StepControl, CheckElement

        # initialize step for in progress projects when step is active
        if (
            not document.isDeleted
            and (
                oldDocument.status != document.status
                and document.status == "1")
        ):
            projects = Project.objects(
                schoolYear=document.schoolYear, isDeleted=False, status='1', phase='1').all()
            for project in projects:
                stepCtrl = StepControl(
                    id=str(document.id),
                    name=document.name,
                    devName=document.devName,
                    tag=document.tag,
                    hasText=document.hasText,
                    hasDate=document.hasDate,
                    hasFile=document.hasFile,
                    hasVideo=document.hasVideo,
                    hasChecklist=document.hasChecklist,
                    hasUpload=document.hasText,
                    text=document.text,
                    file=document.file,
                    video=document.video,
                    approvalType=document.approvalType,
                    sort=document.sort,
                    isStandard=document.isStandard,
                    createdAt=document.createdAt,
                    updatedAt=document.updatedAt
                )
                if document.hasChecklist:
                    for check in document.checklist:
                        stepCtrl.checklist.append(
                            CheckElement(name=check.name, id=check.id))
                project.stepsProgress.steps.append(stepCtrl)
                project.save()

        # delete step for project when step is inactive or deleted
        if (
            (document.isDeleted
                and oldDocument.isDeleted != document.isDeleted)
            or(
                not document.isDeleted
                and (
                    oldDocument.status != document.status
                    and document.status == "2")
            )
        ):
            Project.objects(
                schoolYear=document.schoolYear,
                isDeleted=False, status='1',
                phase='1',
                stepsProgress__steps__id=str(document.id)).update(
                pull__stepsProgress__steps__id=str(document.id))

        # update step values on projects
        if(
            not document.isDeleted
            and document.status == "1"
            and (
                document.name != oldDocument.name
                or document.hasText != oldDocument.hasText
                or document.hasDate != oldDocument.hasDate
                or document.hasFile != oldDocument.hasFile
                or document.hasVideo != oldDocument.hasVideo
                or document.hasChecklist != oldDocument.hasChecklist
                or document.hasUpload != oldDocument.hasUpload
                or document.text != oldDocument.text
                or document.file != oldDocument.file
                or document.video != oldDocument.video
                or document.checklist != oldDocument.checklist
                or document.sort != oldDocument.sort
            )
        ):
            if document.checklist == oldDocument.checklist:
                Project.objects(
                    schoolYear=document.schoolYear,
                    isDeleted=False, status='1',
                    stepsProgress__steps__id=str(document.id)
                ).update(
                    set__stepsProgress__steps__S__hasText=document.hasText,
                    set__stepsProgress__steps__S__hasDate=document.hasDate,
                    set__stepsProgress__steps__S__hasFile=document.hasFile,
                    set__stepsProgress__steps__S__hasVideo=document.hasVideo,
                    set__stepsProgress__steps__S__hasChecklist=document.hasChecklist,
                    set__stepsProgress__steps__S__hasUpload=document.hasUpload,
                    set__stepsProgress__steps__S__name=document.name,
                    set__stepsProgress__steps__S__text=document.text,
                    set__stepsProgress__steps__S__file=document.file,
                    set__stepsProgress__steps__S__video=document.video,
                    set__stepsProgress__steps__S__sort=document.sort
                )
            if document.checklist != oldDocument.checklist:
                projects = Project.objects(
                    schoolYear=document.schoolYear,
                    isDeleted=False, status='1',
                    phase='1',
                    stepsProgress__steps__id=str(document.id)
                )

                for project in projects:
                    step = project.stepsProgress.steps.filter(
                        id=str(document.id)).first()
                    for check in step.checklist:
                        found = False
                        for checkUpd in document.checklist:
                            if check.id == checkUpd.id:
                                check.name = checkUpd.name
                                found = True
                        if not found:
                            step.checklist.remove(check)
                    for checkUpd in document.checklist:
                        found = False
                        for check in step.checklist:
                            if check.id == checkUpd.id:
                                found = True
                        if not found:
                            step.checklist.append(
                                CheckElement(name=checkUpd.name, id=checkUpd.id))
                    project.save()

    def handler_steps_after_create(self, document):
        from app.models.project_model import Project, StepControl, CheckElement

        # initialize steps for in progress projects
        projects = Project.objects(
            schoolYear=document.schoolYear, isDeleted=False, status='1', phase='1').all()
        for project in projects:
            stepCtrl = StepControl(
                id=str(document.pk),
                name=document.name,
                devName=document.devName,
                tag=document.tag,
                hasText=document.hasText,
                hasDate=document.hasDate,
                hasFile=document.hasFile,
                hasVideo=document.hasVideo,
                hasChecklist=document.hasChecklist,
                hasUpload=document.hasText,
                text=document.text,
                file=document.file,
                video=document.video,
                approvalType=document.approvalType,
                sort=document.sort,
                isStandard=document.isStandard,
                createdAt=document.createdAt,
                updatedAt=document.updatedAt
            )
            if document.hasChecklist:
                for check in document.checklist:
                    stepCtrl.checklist.append(
                        CheckElement(name=check.name, id=check.id))
            project.stepsProgress.steps.append(stepCtrl)
            project.save()
