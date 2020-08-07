# app/services/project_service.py


from datetime import datetime

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

        schema = StepControlSchema(partial=True)
        projectSchema = ProjectSchema()

        try:
            documentFiles = getFileFields(StepControl)
            if files and documentFiles:
                validFiles = validate_files(files, documentFiles)
                filesPath = "projects/{}/steps/{}".format(
                    projectId, jsonData['id']
                )
                uploadedfiles = upload_files(validFiles, filesPath)
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

    def handlerCreatePeca(self, projectId):
        from app.models.project_model import Project
        from app.helpers.error_helpers import RegisterNotFound
        from app.schemas.project_schema import ResumePecaSchema

        try:
            project = Project.objects(id=projectId).first()
            if project:
                peca = project.createPeca()

                return ResumePecaSchema().dump(peca), 200
            else:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"recordId": projectId})
        except Exception as e:
            return {'status': 0, 'message': str(e)}, 400

    def createPeca(self, project):
        from app.models.peca_project_model import PecaProject
        from app.models.school_year_model import SchoolYear
        from app.models.shared_embedded_documents import ResumePeca, ResumeSchoolYear
        from app.models.peca_activities_slider_model import ActivitiesSlider

        # create peca project

        schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()

        for peca in project.schoolYears:
            if peca.schoolYear.id == str(schoolYear.id):
                return peca

        reference = project.getReference()
        if not reference.coordinator:
            raise ValidationError(
                {"coordinator": [{"status": "2",
                                  "msg": "Required field"}]}
            )
        if not reference.school:
            raise ValidationError(
                {"school": [{"status": "2",
                             "msg": "Required field"}]}
            )
        if not reference.sponsor:
            raise ValidationError(
                {"sponsor": [{"status": "2",
                              "msg": "Required field"}]}
            )

        pecaProject = PecaProject(
            schoolYear=schoolYear,
            schoolYearName=schoolYear.name,
            project=reference,
            school={
                "name": project.school.name,
                "code": project.school.code,
                "phone": project.school.phone,
                "addressState": str(project.school.addressState.id),
                "addressMunicipality": str(project.school.addressMunicipality.id),
                "address": project.school.address,
                "addressCity": project.school.addressCity,
                "principalFirstName": project.school.principalFirstName,
                "principalLastName": project.school.principalLastName,
                "principalEmail": project.school.principalEmail,
                "principalPhone": project.school.principalPhone,
                "subPrincipalFirstName": project.school.subPrincipalFirstName,
                "subPrincipalLastName": project.school.subPrincipalLastName,
                "subPrincipalEmail": project.school.subPrincipalEmail,
                "subPrincipalPhone": project.school.subPrincipalPhone,
                "nTeachers": project.school.nTeachers,
                "nGrades": project.school.nGrades,
                "nStudents": project.school.nStudents,
                "nAdministrativeStaff": project.school.nAdministrativeStaff,
                "nLaborStaff": project.school.nLaborStaff,
                "facebook": project.school.facebook,
                "instagram": project.school.instagram,
                "twitter": project.school.twitter,
                "slider": project.school.slider,
                "activitiesSlider": ActivitiesSlider(slider=project.school.slider),
                "sections": [
                ]
            }

        )
        pecaProject.save()
        peca = ResumePeca(
            pecaId=str(pecaProject.pk),
            schoolYear=ResumeSchoolYear(
                id=str(schoolYear.id),
                name=schoolYear.name,
                status=schoolYear.status
            )
        )
        project.schoolYears.append(peca)
        project.save()
        return peca

    def handlerProjectBeforeCreate(self, document):

        from app.models.project_model import StepControl, StepsProgress, CheckElement, Approval, Project
        from app.schemas.school_user_schema import SchoolUserSchema
        from app.schemas.coordinator_user_schema import CoordinatorUserSchema
        from app.schemas.sponsor_user_schema import SponsorUserSchema

        year = SchoolYear.objects(status="1", isDeleted=False).first()
        if not year:
            raise ValidationError(
                message="There is not an active school year")
        if not (document.school or document.sponsor or document.coordinator):
            raise ValidationError(
                message="At least an sponsor, school or coordinator is required")
        if document.school:
            duplicated = Project.objects(
                isDeleted=False, school=document.school.id).first()
            if duplicated:
                raise ValidationError(
                    {"school": [{"status": "5",
                                 "msg": "Duplicated school project"}]}
                )
        # validate phase changed
        if document.phase == "2":
            if not document.sponsor:
                raise ValidationError(
                    {"sponsor": [{"status": "2",
                                  "msg": "Required field"}]}
                )
            if not document.school:
                raise ValidationError(
                    {"school": [{"status": "2",
                                 "msg": "Required field"}]}
                )
            if not document.coordinator:
                raise ValidationError(
                    {"coordinator": [{"status": "2",
                                      "msg": "Required field"}]}
                )

        initialSteps = StepsProgress()
        steps = Step.objects(schoolYear=str(year.id),
                             isDeleted=False, status="1").all()
        for step in steps:
            stepCtrl = StepControl(
                id=str(step.id),
                name=step.name,
                devName=step.devName,
                tag=step.tag,
                sort=step.sort,
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
                    stepCtrl.status = "3"
                    stepCtrl.approvalHistory.append(
                        Approval(
                            id="",
                            data=SchoolUserSchema().dump(document.school),
                            status="2"
                        )
                    )
            if document.sponsor:
                if step.devName in ("findSponsor", "coordinatorFillSponsorForm", "schoolFillSponsorForm"):
                    stepCtrl.status = "3"
                    stepCtrl.approvalHistory.append(
                        Approval(
                            id="",
                            data=SponsorUserSchema().dump(document.sponsor),
                            status="2"
                        )
                    )
            if document.coordinator:
                if step.devName in ("findCoordinator", "sponsorFillCoordinatorForm", "schoolFillCoordinatorForm"):
                    stepCtrl.status = "3"
                    stepCtrl.approvalHistory.append(
                        Approval(
                            id="",
                            data=CoordinatorUserSchema().dump(document.coordinator),
                            status="2"
                        )
                    )
            if step.devName == 'corrdinatorCompleteTrainingModules':
                if document.coordinator and document.coordinator.instructed:
                    stepCtrl.status = "3"
            if step.devName == 'coordinatorSendCurriculum':
                if document.coordinator and document.coordinator.curriculum:
                    stepCtrl.status = "3"
                    stepCtrl.approvalHistory.append(
                        Approval(
                            id="",
                            data={
                                "stepHasText": stepCtrl.hasText,
                                "stepHasUpload": stepCtrl.hasUpload,
                                "stepHasDate": stepCtrl.hasDate,
                                "stepHasVideo": stepCtrl.hasVideo,
                                "stepHasChecklist": stepCtrl.hasChecklist,
                                "stepHasFile": stepCtrl.hasFile,
                                "stepText": stepCtrl.text,
                                "stepUploadedFile": {
                                    "name": document.coordinator.curriculum.name,
                                    "url": document.coordinator.curriculum.url}
                            },
                            status="2"
                        )
                    )

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
        from app.models.project_model import Approval, Project
        from app.schemas.school_user_schema import SchoolUserSchema
        from app.schemas.coordinator_user_schema import CoordinatorUserSchema
        from app.schemas.sponsor_user_schema import SponsorUserSchema
        from app.models.peca_project_model import PecaProject
        from app.models.school_year_model import SchoolYear

        # validate phase
        if document.phase == "2":
            if not document.sponsor:
                raise ValidationError(
                    {"sponsor": [{"status": "2",
                                  "msg": "Required field"}]}
                )
            if not document.school:
                raise ValidationError(
                    {"school": [{"status": "2",
                                 "msg": "Required field"}]}
                )
            if not document.coordinator:
                raise ValidationError(
                    {"coordinator": [{"status": "2",
                                      "msg": "Required field"}]}
                )
        if document.sponsor != oldDocument.sponsor:
            if oldDocument.sponsor:
                oldDocument.sponsor.removeProject(document)
            if document.sponsor:
                document.sponsor.addProject(document)
                # steps
                if document.phase == "1":
                    for step in document.stepsProgress.steps:
                        if (
                            step.devName in (
                                "findSponsor",
                                "coordinatorFillSponsorForm",
                                "schoolFillSponsorForm")
                        ):
                            step.status = "3"
                            step.approvalHistory.append(
                                Approval(
                                    id="",
                                    data=SponsorUserSchema().dump(document.sponsor),
                                    status="2"
                                )
                            )
                # peca
                else:
                    schoolYear = SchoolYear.objects(
                        isDeleted=False, status="1").first()
                    if schoolYear:
                        currentPeca = PecaProject.objects(isDeleted=False, project__id=str(
                            document.id), schoolYear=str(schoolYear.id)).first()
                        if currentPeca:
                            currentPeca.project = document.getReference()
                            currentPeca.save()

        if document.school != oldDocument.school:
            if document.school:
                duplicated = Project.objects(
                    isDeleted=False, school=document.school.id, id__ne=document.id).first()
                if duplicated:
                    raise ValidationError(
                        {"school": [{"status": "5",
                                     "msg": "Duplicated school project"}]}
                    )
            if oldDocument.school:
                oldDocument.school.removeProject()
            if document.school:
                document.school.addProject(document)
                if document.phase == "1":
                    for step in document.stepsProgress.steps:
                        if (
                            step.devName in (
                                "findSchool",
                                "coordinatorFillSchoolForm",
                                "sponsorFillSchoollForm")
                        ):
                            step.status = "3"
                            step.approvalHistory.append(
                                Approval(
                                    id="",
                                    data=SchoolUserSchema().dump(document.school),
                                    status="2"
                                )
                            )
                else:
                    schoolYear = SchoolYear.objects(
                        isDeleted=False, status="1").first()
                    if schoolYear:
                        currentPeca = PecaProject.objects(isDeleted=False, project__id=str(
                            document.id), schoolYear=str(schoolYear.id)).first()
                        if currentPeca:
                            currentPeca.project = document.getReference()
                            currentPeca.save()

        if document.coordinator != oldDocument.coordinator:
            if oldDocument.coordinator:
                oldDocument.coordinator.removeProject(document)
            if document.coordinator:
                document.coordinator.addProject(document)
                if document.phase == "1":
                    for step in document.stepsProgress.steps:
                        if (
                            step.devName in (
                                "findCoordinator",
                                "sponsorFillCoordinatorForm",
                                "schoolFillCoordinatorForm")
                        ):
                            step.status = "3"
                            step.approvalHistory.append(
                                Approval(
                                    id="",
                                    data=CoordinatorUserSchema().dump(document.coordinator),
                                    status="2"
                                )
                            )
                        if (
                            step.devName == "corrdinatorCompleteTrainingModules"
                            and document.coordinator.instructed
                        ):
                            step.status = "3"
                        if (
                            step.devName == "coordinatorSendCurriculum"
                            and document.coordinator.curriculum
                        ):
                            step.status = "3"
                            step.approvalHistory.append(
                                Approval(
                                    id="",
                                    data={
                                        "stepHasText": step.hasText,
                                        "stepHasUpload": step.hasUpload,
                                        "stepHasDate": step.hasDate,
                                        "stepHasVideo": step.hasVideo,
                                        "stepHasChecklist": step.hasChecklist,
                                        "stepHasFile": step.hasFile,
                                        "stepText": step.text,
                                        "stepUploadedFile": document.coordinator.curriculum
                                    },
                                    status="2"
                                )
                            )
                else:
                    schoolYear = SchoolYear.objects(
                        isDeleted=False, status="1").first()
                    if schoolYear:
                        currentPeca = PecaProject.objects(isDeleted=False, project__id=str(
                            document.id), schoolYear=str(schoolYear.id)).first()
                        if currentPeca:
                            currentPeca.project = document.getReference()
                            currentPeca.save()
        if document.phase == "1":
            document.stepsProgress.updateProgress()
