# app/services/amblecoin_service.py

from flask import current_app
from marshmallow import ValidationError

from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import AmbleCoins
from app.schemas.peca_setting_schema import AmbleCoinsSchema
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields


class AmbleCoinService():

    def get(self):
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only("pecaSetting").first()

        if schoolYear:
            schema = AmbleCoinsSchema()
            ambleCoins = schoolYear.pecaSetting.lapse1.ambleCoins
            return schema.dump(ambleCoins), 200

    def save(self, jsonData, files=None):

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1")

        if schoolYear:
            try:
                schema = AmbleCoinsSchema()
                documentFiles = getFileFields(AmbleCoins)
                if files and documentFiles:
                    validFiles = validate_files(files, documentFiles)
                    uploadedfiles = upload_files(validFiles)
                    jsonData.update(uploadedfiles)
                data = schema.load(jsonData)

                schoolYear = SchoolYear.objects(
                    isDeleted=False, status="1").first()

                if schoolYear:
                    if not schoolYear.pecaSetting:
                        schoolYear.initFirstPecaSetting()
                    ambleCoins = schoolYear.pecaSetting.lapse1.ambleCoins
                    for field in schema.dump(data).keys():
                        ambleCoins[field] = data[field]
                    try:
                        schoolYear.pecaSetting.lapse1.ambleCoins = ambleCoins
                        schoolYear.save()
                        return schema.dump(ambleCoins), 200
                    except Exception as e:
                        return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
