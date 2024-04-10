# app/services/lapse_planning_service.py


from flask import current_app
from marshmallow import ValidationError
from pymongo import UpdateOne

from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import LapsePlanning
from app.schemas.peca_setting_schema import LapsePlanningSchema
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields


class LapsePlanningService():

    filesPath = 'lapse_planning'

    def get(self, lapse):
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only("pecaSetting").first()

        if schoolYear:
            schema = LapsePlanningSchema()
            lapsePlanning = schoolYear.pecaSetting['lapse{}'.format(
                lapse)].lapsePlanning
            return schema.dump(lapsePlanning), 200

    def save(self, jsonData, lapse, files=None):
        from app.models.peca_project_model import PecaProject

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            try:
                schema = LapsePlanningSchema()
                documentFiles = getFileFields(LapsePlanning)
                if files and documentFiles:
                    validFiles = validate_files(files, documentFiles)
                    uploadedfiles = upload_files(validFiles, self.filesPath)
                    jsonData.update(uploadedfiles)
                data = schema.load(jsonData)
                data.status = jsonData["status"]
                data.devName = jsonData["devName"]
                
                if not schoolYear.pecaSetting:
                    schoolYear.initFirstPecaSetting()

                lapsePlanning = schoolYear.pecaSetting['lapse{}'.format(
                    lapse)].lapsePlanning

                for field in schema.dump(data).keys():
                    lapsePlanning[field] = data[field]
                try:

                    schoolYear.pecaSetting['lapse{}'.format(
                        lapse)].lapsePlanning = lapsePlanning
                    schoolYear.save()

                    if lapsePlanning.status == "1":
                        bulk_operations = []
                        for peca in PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False):

                            lapsePlanningPeca = peca['lapse{}'.format(
                                lapse)].lapsePlanning
                            lapsePlanningPeca.proposalFundationFile = lapsePlanning.proposalFundationFile
                            lapsePlanningPeca.proposalFundationDescription = lapsePlanning.proposalFundationDescription
                            lapsePlanningPeca.meetingDescription = lapsePlanning.meetingDescription
                            lapsePlanningPeca.order = lapsePlanning.order
                            peca['lapse{}'.format(
                                lapse)].lapsePlanning = lapsePlanningPeca
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                        if bulk_operations:
                            PecaProject._get_collection() \
                                .bulk_write(bulk_operations, ordered=False)
                    return schema.dump(lapsePlanning), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
