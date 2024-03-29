# app/services/school_contact_service.py


from .generic_service import *
from app.models.school_user_model import SchoolUser
from app.models.project_model import Project
from app.schemas.school_user_schema import SchoolUserSchema
from app.schemas.sponsor_user_schema import SponsorUserSchema
from app.schemas.project_schema import ProjectSchema


class SchoolContactService(GenericServices):

    def updateRecord(self, recordId, jsonData, partial=False, exclude=(), only=None, files=None):
        """
        Update a record
        """
        schema = self.Schema(exclude=exclude, only=only)
        try:
            documentFiles = getFileFields(self.Model)
            if files and documentFiles:
                validFiles = validate_files(files, documentFiles)
                uploadedfiles = upload_files(validFiles)
                jsonData.update(uploadedfiles)
            data = schema.load(jsonData, partial=partial)
            record = self.getOr404(recordId)
            has_changed = False
            uniquesFields = getUniqueFields(self.Model)
            fieldsForCheckDuplicates = []
            for field in data.keys():
                if data[field] != record[field]:
                    record[field] = data[field]
                    has_changed = True
                    if field in uniquesFields:
                        fieldsForCheckDuplicates.append(
                            {"field": field, "value": data[field]})

            if has_changed:
                isDuplicated = self.checkForDuplicates(
                    fieldsForCheckDuplicates,
                    record.id)
                if isDuplicated:
                    for field in isDuplicated:
                        raise ValidationError(
                            {field["field"]: [{"status": "5",
                                               "msg": "Duplicated record found: {}".format(field["value"])}]}
                        )

                record.save()
            if record.status == "2":
                record = schema.dump(record)
                school = SchoolUser.objects(
                    email=record['email'], isDeleted=False).first()
                project = Project.objects(school=school.id).exclude(
                    'stepsProgress').first()
                projectData = ProjectSchema().dump(project)
                schoolData = SchoolUserSchema().dump(school)
                sponsorData = {}
                if project.sponsor:
                    sponsorData = SponsorUserSchema().dump(project.sponsor)
                return {'record': record, 'project': projectData, 'school': schoolData, 'sponsor': sponsorData}, 200
            else:
                return {'record': schema.dump(record), 'project': {}, 'school': {}, 'sponsor': {}}, 200
        except ValidationError as err:
            return err.messages, 400
