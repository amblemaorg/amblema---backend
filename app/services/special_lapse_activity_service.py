# app/services/special_lapse_activity_service.py

from flask import current_app
from marshmallow import ValidationError
from pymongo import UpdateOne

from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import SpecialLapseActivity
from app.schemas.peca_setting_schema import SpecialLapseActivitySchema
from app.models.peca_special_lapse_activity_model import SpecialActivityPeca
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields


class SpecialLapseActivityService():

    def get(self, lapse):
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only("pecaSetting").first()

        if schoolYear:
            schema = SpecialLapseActivitySchema()
            specialLapseActivity = schoolYear.pecaSetting["lapse{}".format(
                lapse)].specialLapseActivity
            return schema.dump(specialLapseActivity), 200

    def save(self, lapse, jsonData, files=None):
        from app.models.peca_project_model import PecaProject

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            try:
                schema = SpecialLapseActivitySchema()

                data = schema.load(jsonData)

                if not schoolYear.pecaSetting:
                    schoolYear.initFirstPecaSetting()
                specialLapseActivity = schoolYear.pecaSetting['lapse{}'.format(
                    lapse)].specialLapseActivity
                for field in schema.dump(data).keys():
                    specialLapseActivity[field] = data[field]
                try:
                    schoolYear.save()
                    return schema.dump(specialLapseActivity), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
