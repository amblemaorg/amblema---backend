# app/services/lapse_planning_service.py


from flask import current_app
from marshmallow import ValidationError

from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import LapsePlanning
from app.schemas.peca_setting_schema import LapsePlanningSchema
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields


class LapsePlanningService():

    def get(self, lapse):
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only("pecaSetting").first()

        if schoolYear:
            schema = LapsePlanningSchema()
            if lapse == "1":
                lapsePlanning = schoolYear.pecaSetting.lapse1.lapsePlanning
            elif lapse == "2":
                lapsePlanning = schoolYear.pecaSetting.lapse2.lapsePlanning
            elif lapse == "3":
                lapsePlanning = schoolYear.pecaSetting.lapse3.lapsePlanning
            return schema.dump(lapsePlanning), 200

    def save(self, jsonData, lapse, files=None):

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1")

        if schoolYear:
            try:
                schema = LapsePlanningSchema()
                documentFiles = getFileFields(LapsePlanning)
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
                    if lapse == "1":
                        lapsePlanning = schoolYear.pecaSetting.lapse1.lapsePlanning
                    elif lapse == "2":
                        lapsePlanning = schoolYear.pecaSetting.lapse2.lapsePlanning
                    elif lapse == "3":
                        lapsePlanning = schoolYear.pecaSetting.lapse3.lapsePlanning
                    for field in schema.dump(data).keys():
                        lapsePlanning[field] = data[field]
                    try:
                        if lapse == "1":
                            schoolYear.pecaSetting.lapse1.lapsePlanning = lapsePlanning
                        elif lapse == "2":
                            schoolYear.pecaSetting.lapse2.lapsePlanning = lapsePlanning
                        elif lapse == "3":
                            schoolYear.pecaSetting.lapse3.lapsePlanning = lapsePlanning
                        schoolYear.save()
                        return schema.dump(lapsePlanning), 200
                    except Exception as e:
                        return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
