# app/services/peca_project_service.py


from functools import reduce
import operator

from flask import current_app
from marshmallow import ValidationError
from mongoengine import Q

from app.models.school_year_model import SchoolYear
from app.models.peca_project_model import PecaProject
from app.schemas.peca_project_schema import PecaProjectSchema, SchoolSchema
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields
from app.helpers.error_helpers import RegisterNotFound


class PecaProjectService():

    def getAll(self, filters=None):
        if filters:
            filterList = []
            for f in filters:
                if f['field'] == 'school':
                    filterList.append(Q(**{'project__school': f['value']}))
                else:
                    filterList.append(Q(**{f['field']: f['value']}))

            records = PecaProject.objects(isDeleted=False).filter(
                reduce(operator.and_, filterList)).exclude('school')
        else:
            records = PecaProject.objects(isDeleted=False).exclude('school')

        schema = PecaProjectSchema(exclude=('school',))
        return {"records": schema.dump(records, many=True)}, 200

    def get(self, id):

        pecaProject = PecaProject.objects(
            isDeleted=False, id=id).first()
        if pecaProject:
            schema = PecaProjectSchema()
            return schema.dump(pecaProject), 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": id})

    def updateSchool(self, id, jsonData):
        pecaProject = PecaProject.objects(
            isDeleted=False, id=id).first()
        if pecaProject:
            try:
                schema = SchoolSchema(partial=True)
                data = schema.load(jsonData)
                for field in schema.dump(data).keys():
                    pecaProject.school[field] = data[field]
                try:
                    pecaProject.save()
                    return schema.dump(pecaProject.school), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": id})

    def getSchool(self, id):
        pecaProject = PecaProject.objects(
            isDeleted=False, id=id).first()
        if pecaProject:
            try:
                schema = SchoolSchema()
                return schema.dump(pecaProject.school), 200
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": id})

    def initPecaSetting(self, peca):
        from app.models.school_year_model import SchoolYear
        from app.models.peca_amblecoins_model import AmblecoinsPeca, AmbleSection
        from app.models.peca_olympics_model import Olympics
        from app.models.peca_project_model import Lapse
        from app.models.peca_annual_preparation_model import AnnualPreparationPeca

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only('pecaSetting').first()

        for i in range(1, 4):
            peca['lapse{}'.format(i)] = Lapse()
            pecaSettingLapse = schoolYear.pecaSetting['lapse{}'.format(i)]

            if pecaSettingLapse.ambleCoins.status == "1":
                peca['lapse{}'.format(i)].ambleCoins = AmblecoinsPeca()
            else:
                peca['lapse{}'.format(i)].ambleCoins = None

            if pecaSettingLapse.mathOlympic.status == "1":
                peca['lapse{}'.format(i)].olympics = Olympics()
            else:
                peca['lapse{}'.format(i)].olympics = None

            if pecaSettingLapse.annualPreparation.status == "1":
                peca['lapse{}'.format(i)].annualPreparation = AnnualPreparationPeca(
                    step1Description=pecaSettingLapse.annualPreparation.step1Description,
                    step2Description=pecaSettingLapse.annualPreparation.step2Description,
                    step3Description=pecaSettingLapse.annualPreparation.step3Description,
                    step4Description=pecaSettingLapse.annualPreparation.step4Description
                )
            else:
                peca['lapse{}'.format(i)].annualPreparation = None
