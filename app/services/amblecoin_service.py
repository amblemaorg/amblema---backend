# app/services/amblecoin_service.py

from flask import current_app
from marshmallow import ValidationError
from pymongo import UpdateOne

from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import AmbleCoins
from app.schemas.peca_setting_schema import AmbleCoinsSchema
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields


class AmbleCoinService():

    filesPath = 'amblecoins'

    def get(self, lapse):
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only("pecaSetting").first()

        if schoolYear:
            schema = AmbleCoinsSchema()
            ambleCoins = schoolYear.pecaSetting['lapse{}'.format(
                lapse)].ambleCoins
            return schema.dump(ambleCoins), 200

    def save(self, lapse, jsonData, files=None):
        from app.models.peca_project_model import PecaProject

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            try:
                schema = AmbleCoinsSchema()
                documentFiles = getFileFields(AmbleCoins)
                if files and documentFiles:
                    validFiles = validate_files(files, documentFiles)
                    uploadedfiles = upload_files(validFiles, self.filesPath)
                    jsonData.update(uploadedfiles)
                print(jsonData)
                data = schema.load(jsonData)

                if not schoolYear.pecaSetting:
                    schoolYear.initFirstPecaSetting()
                ambleCoins = schoolYear.pecaSetting['lapse{}'.format(
                    lapse)].ambleCoins
                for field in schema.dump(data).keys():
                    ambleCoins[field] = data[field]
                try:
                    schoolYear.pecaSetting['lapse{}'.format(
                        lapse)].ambleCoins = ambleCoins
                    schoolYear.save()
                    if ambleCoins.status == "1":
                        bulk_operations = []
                        for peca in PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False):
                            ambleCoinsPeca = peca['lapse{}'.format(
                                lapse)].ambleCoins
                            ambleCoinsPeca.teachersMeetingFile = ambleCoins.teachersMeetingFile
                            ambleCoinsPeca.teachersMeetingDescription = ambleCoins.teachersMeetingDescription
                            ambleCoinsPeca.piggyBankDescription = ambleCoins.piggyBankDescription
                            ambleCoinsPeca.piggyBankSlider = ambleCoins.piggyBankSlider
                            ambleCoinsPeca.order = ambleCoins.order
                            
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                        if bulk_operations:
                            PecaProject._get_collection() \
                                .bulk_write(bulk_operations, ordered=False)
                    return schema.dump(ambleCoins), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
