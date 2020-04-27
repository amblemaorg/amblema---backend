# app/services/environmental_project_service.py

from flask import current_app
from marshmallow import ValidationError

from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import EnvironmentalProject
from app.schemas.peca_setting_schema import EnvironmentalProjectSchema
from app.helpers.error_helpers import RegisterNotFound


class EnvironmentalProjectService():

    def get(self):
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only("pecaSetting").first()

        if schoolYear:
            schema = EnvironmentalProjectSchema()
            environmentalProject = schoolYear.pecaSetting.environmentalProject
            return schema.dump(environmentalProject), 200
        else:
            raise RegisterNotFound(message="Active school year not found",
                                   status_code=404
                                   )

    def save(self, jsonData):

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            try:
                schema = EnvironmentalProjectSchema()
                data = schema.load(jsonData)

                if not schoolYear.pecaSetting:
                    schoolYear.initFirstPecaSetting()
                environmentalProject = schoolYear.pecaSetting.environmentalProject
                if not environmentalProject:
                    environmentalProject = EnvironmentalProject()
                for field in schema.dump(data).keys():
                    environmentalProject[field] = data[field]
                environmentalProject.validateTarget()
                try:

                    schoolYear.pecaSetting.environmentalProject = environmentalProject
                    schoolYear.save()
                    return schema.dump(environmentalProject), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Active school year not found",
                                   status_code=404
                                   )
