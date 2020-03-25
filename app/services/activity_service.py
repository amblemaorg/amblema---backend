# app/services/activity_service.py


from flask import current_app
from marshmallow import ValidationError

from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import Activity
from app.schemas.peca_setting_schema import ActivitySchema
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
