# app/services/annual_preparation_service.py

from flask import current_app
from marshmallow import ValidationError
from pymongo import UpdateOne

from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import AnnualPreparation
from app.schemas.peca_setting_schema import AnnualPreparationSchema
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields


class AnnualPreparationService():

    filesPath = 'annual_preparation'

    def get(self, lapse):
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only("pecaSetting").first()

        if schoolYear:
            schema = AnnualPreparationSchema()
            annualPreparation = schoolYear.pecaSetting['lapse{}'.format(
                lapse)].annualPreparation
            return schema.dump(annualPreparation), 200

    def save(self, lapse, jsonData, files=None):
        from app.models.peca_project_model import PecaProject

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            try:
                schema = AnnualPreparationSchema()
                documentFiles = getFileFields(AnnualPreparation)
                if files and documentFiles:
                    validFiles = validate_files(files, documentFiles)
                    uploadedfiles = upload_files(validFiles, self.filesPath)
                    jsonData.update(uploadedfiles)
                data = schema.load(jsonData)

                if not schoolYear.pecaSetting:
                    schoolYear.initFirstPecaSetting()
                annualPreparation = schoolYear.pecaSetting['lapse{}'.format(
                    lapse)].annualPreparation
                for field in schema.dump(data).keys():
                    annualPreparation[field] = data[field]
                try:
                    schoolYear.save()
                    if annualPreparation.status == "1":
                        bulk_operations = []
                        for peca in PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False):
                            annualPreparationPeca = peca['lapse{}'.format(
                                lapse)].annualPreparation
                            annualPreparationPeca.step1Description = annualPreparation.step1Description
                            annualPreparationPeca.step2Description = annualPreparation.step2Description
                            annualPreparationPeca.step3Description = annualPreparation.step3Description
                            annualPreparationPeca.step4Description = annualPreparation.step4Description
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                        if bulk_operations:
                            PecaProject._get_collection() \
                                .bulk_write(bulk_operations, ordered=False)
                    return schema.dump(annualPreparation), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
