# app/services/step_service.py


import re

from flask import current_app
from mongoengine import ValidationError
from app.models.school_year_model import SchoolYear


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
                schoolYear=document.schoolYear, isDeleted=False, status='1').all()
            for project in projects:
                stepCtrl = StepControl(
                    id=str(document.id),
                    name=document.name,
                    devName=document.devName,
                    type=document.type,
                    tag=document.tag,
                    text=document.text,
                    date=document.date,
                    file=document.file,
                    video=document.video,
                    createdAt=document.createdAt,
                    updatedAt=document.updatedAt
                )
                if document.type == "5":
                    for check in document.checklist:
                        stepCtrl.checklist.append(
                            CheckElement(name=check.name, id=check.id))
                project.stepsProgress.steps.append(stepCtrl)
                project.save()

        # delete step for froject when step is inactive or deleted
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
                stepsProgress__steps__id=str(document.id)).update(
                pull__stepsProgress__steps__id=str(document.id))

        # update step values on projects
        if(
            not document.isDeleted
            and document.status == "1"
            and (
                document.name != oldDocument.name
                or document.text != oldDocument.text
                or document.date != oldDocument.date
                or document.file != oldDocument.file
                or document.video != oldDocument.video
                or document.checklist != oldDocument.checklist
            )
        ):
            if document.type != "5":
                Project.objects(
                    schoolYear=document.schoolYear,
                    isDeleted=False, status='1',
                    stepsProgress__steps__id=str(document.id)
                ).update(
                    set__stepsProgress__steps__S__name=document.name,
                    set__stepsProgress__steps__S__text=document.text,
                    set__stepsProgress__steps__S__date=document.date,
                    set__stepsProgress__steps__S__file=document.file,
                    set__stepsProgress__steps__S__video=document.video
                )
            if document.type == "5":
                projects = Project.objects(
                    schoolYear=document.schoolYear,
                    isDeleted=False, status='1',
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
            schoolYear=document.schoolYear, isDeleted=False, status='1').all()
        for project in projects:
            stepCtrl = StepControl(
                id=str(document.id),
                name=document.name,
                devName=document.devName,
                type=document.type,
                tag=document.tag,
                text=document.text,
                date=document.date,
                file=document.file,
                video=document.video,
                isStandard=document.isStandard,
                createdAt=document.createdAt,
                updatedAt=document.updatedAt
            )
            if document.type == "5":
                for check in document.checklist:
                    stepCtrl.checklist.append(
                        CheckElement(name=check.name, id=check.id))
            project.stepsProgress.steps.append(stepCtrl)
            project.save()
