# app/services/school_slider_service.py


import re

from flask import current_app
from marshmallow import ValidationError

from app.models.school_user_model import SchoolUser
from app.models.shared_embedded_documents import ImageStatus
from app.schemas.shared_schemas import ImageStatusSchema

from app.helpers.error_helpers import RegisterNotFound
from app.models.request_content_approval_model import RequestContentApproval


class SchoolSliderService():
    def get(self, schoolId):

        school = SchoolUser.objects(
            isDeleted=False, id=schoolId).first()

        if school:
            schema = ImageStatusSchema()
            return {"records": schema.dump(school.slider, many=True)}, 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": schoolId})

    def save(self, schoolId, userId, jsonData):
        from app.models.user_model import User
        from app.models.shared_embedded_documents import Approval

        school = SchoolUser.objects(
            isDeleted=False, id=schoolId).first()

        if school:
            try:
                schema = ImageStatusSchema()
                data = schema.load(jsonData)

                user = User.objects(id=userId, isDeleted=False).first()
                if not user:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"userId":  userId})

                image = ImageStatus()
                data['schoolId'] = schoolId
                for field in schema.dump(data).keys():
                    image[field] = data[field]
                try:
                    request = RequestContentApproval(
                        project=school.project,
                        user=user,
                        type="4",
                        detail=schema.dump(image)
                    ).save()
                    image.approvalHistory = Approval(
                        id=str(request.id),
                        user=user,
                        detail=data
                    )
                    school.slider.append(image)
                    school.save()

                    return schema.dump(image), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": schoolId})

    def update(self, schoolId, sliderId, jsonData):

        school = SchoolUser.objects(
            isDeleted=False,
            id=schoolId,
            slider__id=sliderId,
            slider__isDeleted=False).first()

        if school:
            try:
                schema = ImageStatusSchema()
                data = schema.load(jsonData, partial=True)

                hasChanged = False

                for slider in school.slider:
                    if str(slider.id) == sliderId and not slider.isDeleted:
                        for field in schema.dump(data).keys():
                            if slider[field] != data[field]:
                                hasChanged = True
                                slider[field] = data[field]

                        if hasChanged:
                            try:
                                school.save()
                                return schema.dump(slider), 200
                            except Exception as e:
                                return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"schoolId": schoolId, "sliderId": sliderId})

    def delete(self, schoolId, sliderId):
        """
        Delete (change isDeleted to False) a record
        """

        school = SchoolUser.objects(
            isDeleted=False,
            id=schoolId,
            slider__id=sliderId,
            slider__isDeleted=False).first()

        if school:
            try:
                for slider in school.slider:
                    if str(slider.id) == sliderId and not slider.isDeleted:
                        slider.isDeleted = True
                        try:
                            school.save()
                            return {"msg": "Record successfully deleted"}, 200
                        except Exception as e:
                            return {'status': 0, 'message': str(e)}, 400
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"schoolId": schoolId, "sliderId": sliderId})
