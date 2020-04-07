# app/services/activity_service.py


import re

from flask import current_app
from marshmallow import ValidationError

from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import Activity
from app.schemas.peca_setting_schema import ActivitySchema
from app.schemas.activity_schema import ActivitySummarySchema, ActivityHandleStatus
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields
from app.helpers.error_helpers import RegisterNotFound


class ActivityService():

    def get(self, lapse, id):
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only("pecaSetting").first()

        if schoolYear:
            schema = ActivitySchema()
            if lapse == "1":
                activities = schoolYear.pecaSetting.lapse1.activities
            elif lapse == "2":
                activities = schoolYear.pecaSetting.lapse2.activities
            elif lapse == "3":
                activities = schoolYear.pecaSetting.lapse3.activities

            for activity in activities:
                if str(activity.id) == str(id) and not activity.isDeleted:
                    return schema.dump(activity), 200
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": id})

    def save(self, lapse, jsonData, files=None):

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            try:
                schema = ActivitySchema()
                documentFiles = getFileFields(Activity)
                if files and documentFiles:
                    validFiles = validate_files(files, documentFiles)
                    uploadedfiles = upload_files(validFiles)
                    jsonData.update(uploadedfiles)
                data = schema.load(jsonData)

                if not schoolYear.pecaSetting:
                    schoolYear.initFirstPecaSetting()

                activity = Activity()
                for field in schema.dump(data).keys():
                    activity[field] = data[field]
                activity.devName = re.sub(
                    r'[\W_]', '_', activity.name.strip().lower())
                try:
                    if lapse == "1":
                        schoolYear.pecaSetting.lapse1.activities.append(
                            activity)
                    elif lapse == "2":
                        schoolYear.pecaSetting.lapse2.activities.append(
                            activity)
                    elif lapse == "3":
                        schoolYear.pecaSetting.lapse3.activities.append(
                            activity)
                    schoolYear.save()
                    return schema.dump(activity), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400

    def update(self, lapse, id, jsonData, files=None):

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            try:
                schema = ActivitySchema()
                documentFiles = getFileFields(Activity)
                if files and documentFiles:
                    validFiles = validate_files(files, documentFiles)
                    uploadedfiles = upload_files(validFiles)
                    jsonData.update(uploadedfiles)
                data = schema.load(jsonData, partial=True)

                if lapse == "1":
                    activities = schoolYear.pecaSetting.lapse1.activities
                elif lapse == "2":
                    activities = schoolYear.pecaSetting.lapse2.activities
                elif lapse == "3":
                    activities = schoolYear.pecaSetting.lapse3.activities

                found = False
                hasChanged = False
                for activity in activities:
                    if str(activity.id) == str(id) and not activity.isDeleted:
                        found = True
                        for field in schema.dump(data).keys():
                            if activity[field] != data[field]:
                                hasChanged = True
                                activity[field] = data[field]
                if not found:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"recordId": id})

                if hasChanged:
                    try:
                        if lapse == "1":
                            schoolYear.pecaSetting.lapse1.activities = activities
                        elif lapse == "2":
                            schoolYear.pecaSetting.lapse2.activities = activities
                        elif lapse == "3":
                            schoolYear.pecaSetting.lapse3.activities = activities
                        schoolYear.save()
                    except Exception as e:
                        return {'status': 0, 'message': str(e)}, 400

                return schema.dump(activity), 200

            except ValidationError as err:
                return err.normalized_messages(), 400

    def delete(self, lapse, id):
        """
        Delete (change isDeleted to False) a record
        """

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            if lapse == "1":
                activities = schoolYear.pecaSetting.lapse1.activities
            elif lapse == "2":
                activities = schoolYear.pecaSetting.lapse2.activities
            elif lapse == "3":
                activities = schoolYear.pecaSetting.lapse3.activities

            found = False
            for activity in activities:
                if str(activity.id) == str(id) and not activity.isDeleted:
                    found = True
                    try:
                        activity.isDeleted = True
                        if lapse == "1":
                            schoolYear.pecaSetting.lapse1.activities = activities
                        elif lapse == "2":
                            schoolYear.pecaSetting.lapse2.activities = activities
                        elif lapse == "3":
                            schoolYear.pecaSetting.lapse3.activities = activities
                        schoolYear.save()
                        return {"message": "Record deleted successfully"}, 200
                    except Exception as e:
                        return {'status': 0, 'message': str(e)}, 400

            if not found:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"recordId": id})

    def getSumary(self, filters=()):

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            current_app.logger.info(filters)
            records = {
                'lapse1': [],
                'lapse2': [],
                'lapse3': []
            }
            schema = ActivitySummarySchema()
            for i in range(3):

                initialWorkshop = schoolYear.pecaSetting['lapse{}'.format(
                    i+1)].initialWorkshop
                if (
                    (not filters) or
                    ('status' in filters and filters['status']
                     == '1' and initialWorkshop.status == '1')
                ):
                    data = {
                        "name": "Taller inicial",
                        "devName": "initialWorkshop",
                        "isStandard": True,
                        "status": initialWorkshop.status
                    }
                    records['lapse{}'.format(i+1)].append(schema.dump(data))

                ambleCoins = schoolYear.pecaSetting['lapse{}'.format(
                    i+1)].ambleCoins
                if (
                    (not filters) or
                    ('status' in filters and filters['status']
                     == '1' and ambleCoins.status == '1')
                ):

                    data = {
                        "name": "AmbLeMonedas",
                        "devName": "ambleCoins",
                        "isStandard": True,
                        "status": ambleCoins.status
                    }
                    records['lapse{}'.format(i+1)].append(schema.dump(data))

                lapsePlanning = schoolYear.pecaSetting['lapse{}'.format(
                    i+1)].lapsePlanning
                if (
                    (not filters) or
                    ('status' in filters and filters['status']
                     == '1' and lapsePlanning.status == '1')
                ):
                    data = {
                        "name": "Planificación de lapso",
                        "devName": "lapsePlanning",
                        "isStandard": True,
                        "status": lapsePlanning.status
                    }
                    records['lapse{}'.format(i+1)].append(schema.dump(data))

                annualConvention = schoolYear.pecaSetting['lapse{}'.format(
                    i+1)].annualConvention

                if (
                    (not filters) or
                    ('status' in filters and filters['status']
                     == '1' and annualConvention.status == '1')
                ):

                    data = {
                        "name": "Convención anual",
                        "devName": "annualConvention",
                        "isStandard": True,
                        "status": annualConvention.status
                    }
                    records['lapse{}'.format(i+1)].append(schema.dump(data))

                for activity in schoolYear.pecaSetting['lapse{}'.format(i+1)].activities:
                    if (
                        (not filters) or
                        ('status' in filters and filters['status']
                         == '1' and activity.status == '1')
                    ):
                        data = {
                            "id": str(activity.id),
                            "name": activity.name,
                            "devName": activity.devName,
                            "isStandard": False,
                            "status": activity.status
                        }
                        records['lapse{}'.format(
                            i+1)].append(schema.dump(data))
            return records, 200

        else:
            raise RegisterNotFound(message="Active school year not found",
                                   status_code=404
                                   )

    def handleEnable(self, jsonData):
        """
        Update status active/inactive of activities per lapse
        Params:
          id: devName in case of standard. id in case of not standard
          jsonData:
              lapse: 1,2,3
              isStandard: boolean
              status: 1=active 2=inactive
        """

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            schema = ActivityHandleStatus()
            try:
                data = schema.load(jsonData)
                current_app.logger.info(data)
                found = False
                if data['isStandard']:
                    if data['id'] == "initialWorkshop":
                        found = True
                        schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].initialWorkshop.status = data['status']

                    elif data['id'] == "ambleCoins":
                        found = True
                        schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].ambleCoins.status = data['status']

                    elif data['id'] == "lapsePlanning":
                        found = True
                        schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].lapsePlanning.status = data['status']

                    elif data['id'] == "annualConvention":
                        found = True
                        schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].annualConvention.status = data['status']
                else:
                    for activity in schoolYear.pecaSetting['lapse{}'.format(data['lapse'])].activities:
                        if str(activity.id) == data['id']:
                            found = True
                            activity.status = data['status']
                            break
                if found:
                    current_app.logger.info(
                        schoolYear.pecaSetting.lapse1.ambleCoins.status)
                    schoolYear.save()
                    schoolYear = SchoolYear.objects.get(id=schoolYear.id)
                    current_app.logger.info(
                        schoolYear.pecaSetting.lapse1.ambleCoins.status)
                    current_app.logger.info(schoolYear.id)
                    return {"msg": "Record updated"}, 200
                else:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"recordId": data['id']})

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Active school year not found",
                                   status_code=404)
