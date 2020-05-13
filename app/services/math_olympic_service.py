# app/services/math_olimpic_service.py

from flask import current_app
from marshmallow import ValidationError

from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import MathOlympic
from app.schemas.peca_setting_schema import MathOlympicSchema
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields


class MathOlympicService():

    filesPath = 'math_olympics'

    def get(self, lapse):
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only("pecaSetting").first()

        if schoolYear:
            schema = MathOlympicSchema()
            mathOlympic = schoolYear.pecaSetting['lapse{}'.format(
                lapse)].mathOlympic
            return schema.dump(mathOlympic), 200

    def save(self, lapse, jsonData, files=None):

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            try:
                schema = MathOlympicSchema()
                documentFiles = getFileFields(MathOlympic)
                if files and documentFiles:
                    validFiles = validate_files(files, documentFiles)
                    uploadedfiles = upload_files(validFiles, self.filesPath)
                    jsonData.update(uploadedfiles)
                data = schema.load(jsonData)

                if not schoolYear.pecaSetting:
                    schoolYear.initFirstPecaSetting()
                mathOlympic = schoolYear.pecaSetting['lapse{}'.format(
                    lapse)].mathOlympic
                for field in schema.dump(data).keys():
                    mathOlympic[field] = data[field]
                try:
                    schoolYear.pecaSetting['lapse{}'.format(
                        lapse)].mathOlympic = mathOlympic
                    schoolYear.save()
                    return schema.dump(mathOlympic), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
