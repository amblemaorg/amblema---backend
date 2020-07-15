# app/services/user_service.py


from flask import current_app
from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q

from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields, getFileFields
from app.helpers.handler_files import validate_files, upload_files
from app.services.generic_service import GenericServices
from app.blueprints.web_content.models.web_content import WebContent


class UserService(GenericServices):

    def saveRecord(self, jsonData):
        """
        Method that saves a new record.   
        params: jsonData
        """
        schema = self.Schema()
        try:
            data = schema.load(jsonData)
            password = data['password']
            uniquesFields = getUniqueFields(self.Model)
            fieldsForCheckDuplicates = []
            record = self.Model()
            for field in data.keys():
                record[field] = data[field]
                if field in uniquesFields:
                    fieldsForCheckDuplicates.append(
                        {"field": field, "value": data[field]})
            isDuplicated = self.checkForDuplicates(
                fieldsForCheckDuplicates, record.id)
            if isDuplicated:
                for field in isDuplicated:
                    raise ValidationError(
                        {field["field"]: [{"status": "5",
                                           "msg": "Duplicated record found: {}".format(field["value"])}]}
                    )
            try:
                record.setHashPassword()
                record.save()
                record.sendRegistrationEmail(password)
                if self.Model.__name__ == 'SchoolUser':
                    WebContent.objects().update(
                        inc__homePage__nSchools=1
                    )
                elif self.Model.__name__ == 'SponsorUser':
                    WebContent.objects().update(
                        inc__homePage__nSponsors=1
                    )
                return schema.dump(record), 201
            except Exception as e:
                return {'status': 0, 'message': str(e)}, 400
        except ValidationError as err:
            return err.normalized_messages(), 400

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
            if "password" in data:
                record.setHashPassword()
                has_changed = True

            if has_changed:
                isDuplicated = self.checkForDuplicates(
                    fieldsForCheckDuplicates, record.id)
                if isDuplicated:
                    for field in isDuplicated:
                        raise ValidationError(
                            {field["field"]: [{"status": "5",
                                               "msg": "Duplicated record found: {}".format(field["value"])}]}
                        )

                record.save()

            return schema.dump(record), 200
        except ValidationError as err:
            return err.messages, 400

    def deleteRecord(self, recordId):
        """
        Delete (change status False) a record
        """

        from app.models.project_model import Project
        from app.models.peca_project_model import PecaProject
        from app.models.request_content_approval_model import RequestContentApproval
        from app.models.request_find_coordinator_model import RequestFindCoordinator
        from app.models.request_find_sponsor_model import RequestFindSponsor
        from app.models.request_find_school_model import RequestFindSchool

        record = self.getOr404(recordId)

        amblemaEntities = ['SchoolUser', 'SponsorUser', 'CoordinatorUser']
        entity = ''
        if self.Model.__name__ in amblemaEntities:
            if self.Model.__name__ == 'SchoolUser':
                project = Project.objects(
                    school=recordId, isDeleted=False).first()
                if project:
                    entity = 'Project'
                else:
                    peca = PecaProject.objects(
                        isDeleted=False, project__school__id=recordId).first()
                    if peca:
                        entity = 'PecaProject'
            elif self.Model.__name__ == 'SponsorUser':

                project = Project.objects(
                    sponsor=recordId, isDeleted=False).first()
                if project:
                    entity = 'Project'
                else:
                    peca = PecaProject.objects(
                        isDeleted=False, project__sponsor__id=recordId).first()
                    if peca:
                        entity = 'PecaProject'
            elif self.Model.__name__ == 'CoordinatorUser':
                project = Project.objects(
                    coordinator=recordId, isDeleted=False).first()
                if project:
                    entity = 'Project'
                else:
                    peca = PecaProject.objects(
                        isDeleted=False, project__coordinator__id=recordId).first()
                    if peca:
                        entity = 'PecaProject'
            if not entity:
                contentRequest = RequestContentApproval.objects(
                    isDeleted=False, user=recordId, status="1").first()
                if contentRequest:
                    entity = 'RequestContentApproval'
                else:
                    findSchool = RequestFindSchool.objects(
                        isDeleted=False, user=recordId, status="1").first()
                    if findSchool:
                        entity = 'RequestFindSchool'
                    else:
                        findSponsor = RequestFindSponsor.objects(
                            isDeleted=False, user=recordId, status="1").first()
                        if findSponsor:
                            entity = 'RequestFindSponsor'
                        else:
                            findCoordinator = RequestFindCoordinator.objects(
                                isDeleted=False, user=recordId, status="1").first()
                            if findCoordinator:
                                entity = 'RequestFindCoordinator'
        if entity:
            return {
                'status': '0',
                'entity': entity,
                'msg': 'Record has an active related entity'
            }, 419

        try:
            record.isDeleted = True
            record.save()
            if self.Model.__name__ == 'SchoolUser':
                WebContent.objects().update(
                    dec__homePage__nSchools=1
                )
            elif self.Model.__name__ == 'SponsorUser':
                WebContent.objects().update(
                    dec__homePage__nSponsors=1
                )

        except Exception as e:
            return {'status': 0, 'message': str(e)}, 400

        return {"message": "Record deleted successfully"}, 200
