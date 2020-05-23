# app/services/initial_workshop_service.py

from flask import current_app
from marshmallow import ValidationError
from pymongo import UpdateOne

from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import InitialWorshop
from app.schemas.peca_setting_schema import InicialWorkshopSchema
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields


class InicialWorkshopService():

    def get(self, lapse):
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only("pecaSetting").first()

        if schoolYear:
            schema = InicialWorkshopSchema()
            initialWorkshop = schoolYear.pecaSetting["lapse{}".format(
                lapse)].initialWorkshop
            return schema.dump(initialWorkshop), 200

    def save(self, lapse, jsonData, files=None):
        from app.models.peca_project_model import PecaProject

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            try:
                schema = InicialWorkshopSchema()
                documentFiles = getFileFields(InitialWorshop)
                if files and documentFiles:
                    validFiles = validate_files(files, documentFiles)
                    folder = 'initial_workshop'
                    uploadedfiles = upload_files(validFiles, folder)
                    jsonData.update(uploadedfiles)
                data = schema.load(jsonData)

                if not schoolYear.pecaSetting:
                    schoolYear.initFirstPecaSetting()
                initialWorkshop = schoolYear.pecaSetting['lapse{}'.format(
                    lapse)].initialWorkshop
                for field in schema.dump(data).keys():
                    initialWorkshop[field] = data[field]
                try:
                    schoolYear.pecaSetting['lapse{}'.format(
                        lapse)].initialWorkshop = initialWorkshop
                    schoolYear.save()
                    if initialWorkshop.status == "1":

                        bulk_operations = []
                        for peca in PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False):

                            initialWorkshopPeca = peca['lapse{}'.format(
                                lapse)].initialWorkshop
                            initialWorkshopPeca.agreementFile = initialWorkshop.agreementFile
                            initialWorkshopPeca.agreementDescription = initialWorkshop.agreementDescription
                            initialWorkshopPeca.planningMeetingFile = initialWorkshop.planningMeetingFile
                            initialWorkshopPeca.planningMeetingDescription = initialWorkshop.planningMeetingDescription
                            initialWorkshopPeca.teachersMeetingFile = initialWorkshop.teachersMeetingFile
                            initialWorkshopPeca.teachersMeetingDescription = initialWorkshop.teachersMeetingDescription
                            peca['lapse{}'.format(
                                lapse)].initialWorkshop = initialWorkshopPeca
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                        if bulk_operations:
                            PecaProject._get_collection() \
                                .bulk_write(bulk_operations, ordered=False)
                    return schema.dump(initialWorkshop), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
