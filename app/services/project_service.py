# app/services/project_service.py


from marshmallow import ValidationError

from app.schemas.project_schema import StepControlSchema, ProjectSchema
from app.models.project_model import Project, StepControl
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
