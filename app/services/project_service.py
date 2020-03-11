# app/services/project_service.py


from flask import current_app
from marshmallow import ValidationError

from app.schemas.project_schema import StepControlSchema, ProjectSchema
from app.models.school_year_model import SchoolYear
from app.models.step_model import Step
from app.helpers.document_metadata import getFileFields
from app.helpers.handler_files import validate_files, upload_files


class ProjectService():

    def updateStep(self, projectId, jsonData, files=None):
        """Update a step in a project.
          Params:
            projectId: str
            data: {
                "id": str stepId,
                "status": str,
                "date": str,
                "uploadedFile": {"url": str, "name"},
                "checklist": [{"id": str, "name":str, "checked": bool}]}
        """
        from app.models.project_model import Project, StepControl

        schema = StepControlSchema()
        projectSchema = ProjectSchema()

        try:
            documentFiles = getFileFields(StepControl)
            if files and documentFiles:
                validFiles = validate_files(files, documentFiles)
                uploadedfiles = upload_files(validFiles)
                jsonData.update(uploadedfiles)
            data = schema.load(jsonData)
            project = Project.objects(
                id=projectId, isDeleted=False, status="1").first()
            if not project:
                raise ValidationError(
                    {"projectId": [{"status": "6",
                                    "msg": "Record not found"}]}
                )
            project.updateStep(data)
            return projectSchema.dump(project)
        except ValidationError as err:
            return err.normalized_messages(), 400

    def handlerProjectBeforeCreate(self, document):

        from app.models.project_model import StepControl, StepsProgress, CheckElement

        year = SchoolYear.objects(status="1", isDeleted=False).first()
        if not year:
            raise ValidationError(
                message="There is not an active school year")
        if not (document.school or document.sponsor or document.coordinator):
            raise ValidationError(
                message="At least an sponsor, school or coordinator is required")
        initialSteps = StepsProgress()
        steps = Step.objects(schoolYear=str(year.id)).all()
        for step in steps:
            stepCtrl = StepControl(
                id=str(step.id),
                name=step.name,
                devName=step.devName,
                tag=step.tag,
                approvalType=step.approvalType,
                hasText=step.hasText,
                hasFile=step.hasFile,
                hasDate=step.hasDate,
                hasVideo=step.hasVideo,
                hasChecklist=step.hasChecklist,
                hasUpload=step.hasUpload,
                text=step.text,
                file=step.file,
                video=step.video,
                createdAt=step.createdAt,
                updatedAt=step.updatedAt
            )
            if step.hasChecklist:
                for check in step.checklist:
                    stepCtrl.checklist.append(
                        CheckElement(name=check.name, id=check.id))
            if document.school:
                if step.devName in ("findSchool", "coordinatorFillSchoolForm", "sponsorFillSchoolForm"):
                    stepCtrl.status = "2"
            if document.sponsor:
                if step.devName in ("findSponsor", "coordinatorFillSponsorForm", "schoolFillSponsorlForm"):
                    stepCtrl.status = "2"
            if document.coordinator:
                if step.devName in ("findCoordinator", "sponsorFillCoordinatorForm", "schoolFillCoordinatorForm"):
                    stepCtrl.status = "2"
            initialSteps.steps.append(stepCtrl)
        document.stepsProgress = initialSteps
        document.schoolYear = year
        document.stepsProgress.updateProgress()

    def handlerProjectAfterCreate(self, document):
        if document.sponsor:
            document.sponsor.addProject(document)
        if document.coordinator:
            document.coordinator.addProject(document)
        if document.school:
            document.school.addProject(document)

    def handlerProjectBeforeUpdate(self, document, oldDocument):

        if document.sponsor != oldDocument.sponsor:
            if oldDocument.sponsor:
                oldDocument.sponsor.removeProject(document)
            if document.sponsor:
                document.sponsor.addProject(document)
                for step in document.stepsProgress.steps:
                    if (
                        step.devName in (
                            "findSponsor",
                            "coordinatorFillSponsorForm",
                            "schoolFillSponsorlForm")
                    ):
                        step.status = "2"

        if document.school != oldDocument.school:
            if oldDocument.school:
                oldDocument.school.removeProject()
            if document.school:
                document.school.addProject(document)
                for step in document.stepsProgress.steps:
                    if (
                        step.devName in (
                            "findSchool",
                            "coordinatorFillSchoolForm",
                            "sponsorFillSchoollForm")
                    ):
                        step.status = "2"

        if document.coordinator != oldDocument.coordinator:
            if oldDocument.coordinator:
                oldDocument.coordinator.removeProject(document)
            if document.coordinator:
                document.coordinator.addProject(document)
                for step in document.stepsProgress.steps:
                    if (
                        step.devName in (
                            "findSchool",
                            "coordinatorFillSchoolForm",
                            "schoolFillSchoollForm")
                    ):
                        step.status = "2"
                    if (
                        step.devName == "corrdinatorCompleteTrainingModules"
                        and document.coordinator.instructed
                    ):
                        step.status = "2"

        document.stepsProgress.updateProgress()
