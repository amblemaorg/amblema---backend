# app/services/annual_convention_service.py

from flask import current_app
from marshmallow import ValidationError
from pymongo import UpdateOne

from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import AnnualConvention
from app.schemas.peca_setting_schema import AnnualConventionSchema
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields


class AnnualConventionService():

    filesPath = 'annual_convention'

    def get(self, lapse):
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only("pecaSetting").first()

        if schoolYear:
            schema = AnnualConventionSchema()
            annualConvention = schoolYear.pecaSetting['lapse{}'.format(
                lapse)].annualConvention
            return schema.dump(annualConvention), 200

    def save(self, lapse, jsonData, files=None):
        from app.models.peca_project_model import PecaProject

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            try:
                schema = AnnualConventionSchema()
                data = schema.load(jsonData)

                if not schoolYear.pecaSetting:
                    schoolYear.initFirstPecaSetting()
                annualConvention = schoolYear.pecaSetting['lapse{}'.format(
                    lapse)].annualConvention
                oldChecklist = annualConvention.checklist
                for field in schema.dump(data).keys():
                    annualConvention[field] = data[field]
                try:
                    schoolYear.pecaSetting['lapse{}'.format(
                        lapse)].annualConvention = annualConvention
                    schoolYear.save()
                    if annualConvention.status == "1":
                        from app.models.shared_embedded_documents import CheckElement

                        oldIds = []
                        for reg in oldChecklist:
                            oldIds.append(str(reg.id))
                        newIds = {}
                        for reg in schoolYear.pecaSetting['lapse{}'.format(lapse)].annualConvention.checklist:
                            newIds[str(reg.id)] = reg
                        bulk_operations = []
                        for peca in PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False):
                            updated = False
                            pecaRegs = []
                            peca['lapse{}'.format(lapse)].annualConvention.order = annualConvention.order
                            print("order ", peca['lapse{}'.format(lapse)].annualConvention.order)
                            print("order ", annualConvention.order)
                            
                            for reg in peca['lapse{}'.format(lapse)].annualConvention.checklist:
                                if str(reg.id) in oldIds and str(reg.id) not in newIds:
                                    peca['lapse{}'.format(
                                        lapse)].annualConvention.checklist.remove(reg)
                                    updated = True
                                if str(reg.id) in newIds and reg.name != newIds[str(reg.id)].name:
                                    reg.name = newIds[str(reg.id)].name
                                    updated = True
                                pecaRegs.append(str(reg.id))
                            for key in newIds.keys():
                                if str(key) not in pecaRegs:
                                    peca['lapse{}'.format(lapse)].annualConvention.checklist.append(
                                        CheckElement(
                                            id=str(newIds[key].id),
                                            name=newIds[key].name
                                        )
                                    )
                                    updated = True
                            #if updated:
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                        if bulk_operations:
                            PecaProject._get_collection() \
                                .bulk_write(bulk_operations, ordered=False)

                    return schema.dump(annualConvention), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
