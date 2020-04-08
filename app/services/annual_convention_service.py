# app/services/annual_convention_service.py

from flask import current_app
from marshmallow import ValidationError

from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import AnnualConvention
from app.schemas.peca_setting_schema import AnnualConventionSchema
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields


class AnnualConventionService():

    def get(self, lapse):
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only("pecaSetting").first()

        if schoolYear:
            schema = AnnualConventionSchema()
            annualConvention = schoolYear.pecaSetting['lapse{}'.format(
                lapse)].annualConvention
            return schema.dump(annualConvention), 200

    def save(self, lapse, jsonData, files=None):

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            try:
                schema = AnnualConventionSchema()
                documentFiles = getFileFields(AnnualConvention)
                if files and documentFiles:
                    validFiles = validate_files(files, documentFiles)
                    uploadedfiles = upload_files(validFiles)
                    jsonData.update(uploadedfiles)
                data = schema.load(jsonData)

                if not schoolYear.pecaSetting:
                    schoolYear.initFirstPecaSetting()
                annualConvention = schoolYear.pecaSetting['lapse{}'.format(
                    lapse)].annualConvention
                for field in schema.dump(data).keys():
                    annualConvention[field] = data[field]
                try:
                    schoolYear.pecaSetting['lapse{}'.format(
                        lapse)].annualConvention = annualConvention
                    schoolYear.save()
                    return schema.dump(annualConvention), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
