# app/services/math_olimpic_service.py

from flask import current_app
from marshmallow import ValidationError
from pymongo import UpdateOne

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
        from app.models.peca_project_model import PecaProject

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
                    schoolYear.save()
                    if mathOlympic.status == "1":
                        bulk_operations = []
                        for peca in PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False):
                            olympicsPeca = peca['lapse{}'.format(
                                lapse)].olympics
                            olympicsPeca.description = mathOlympic.description
                            olympicsPeca.file = mathOlympic.file
                            olympicsPeca.date = mathOlympic.date
                            if mathOlympic.date and mathOlympic.date != olympicsPeca.date:
                                peca.scheduleActivity(
                                    devName="olympics__date",
                                    subject="Olimpíadas matemáticas",
                                    startTime=mathOlympic.date,
                                    description="Fecha del evento"
                                )
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                        if bulk_operations:
                            PecaProject._get_collection() \
                                .bulk_write(bulk_operations, ordered=False)
                    return schema.dump(mathOlympic), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
