# app/services/school_slider_service.py


import re

from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.models.shared_embedded_documents import ImageStatus
from app.schemas.shared_schemas import ImageStatusSchema

from app.helpers.error_helpers import RegisterNotFound


class SchoolSliderService():

    def save(self, pecaId, jsonData):

        peca = PecaProject.objects(
            isDeleted=False, id=pecaId).first()

        if peca:
            try:
                schema = ImageStatusSchema()
                data = schema.load(jsonData)

                image = ImageStatus()
                for field in schema.dump(data).keys():
                    image[field] = data[field]
                try:
                    peca.school.slider.append(image)
                    peca.save()
                    return schema.dump(image), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": pecaId})

    def update(self, pecaId, sliderId, jsonData):

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
            school__slider__id=sliderId,
            school__slider__isDeleted=False).first()

        if peca:
            try:
                schema = ImageStatusSchema()
                data = schema.load(jsonData, partial=True)

                hasChanged = False

                for slider in peca.school.slider:
                    if str(slider.id) == sliderId and not slider.isDeleted:
                        for field in schema.dump(data).keys():
                            if slider[field] != data[field]:
                                hasChanged = True
                                slider[field] = data[field]

                        if hasChanged:
                            try:
                                peca.save()
                                return schema.dump(slider), 200
                            except Exception as e:
                                return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId, "sliderId": sliderId})

    def delete(self, pecaId, sliderId):
        """
        Delete (change isDeleted to False) a record
        """

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
            school__slider__id=sliderId,
            school__slider__isDeleted=False).first()

        if peca:
            try:
                for slider in peca.school.slider:
                    if str(slider.id) == sliderId and not slider.isDeleted:
                        slider.isDeleted = True
                        try:
                            peca.save()
                            return {"msg": "Record successfully deleted"}, 200
                        except Exception as e:
                            return {'status': 0, 'message': str(e)}, 400
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId, "sliderId": sliderId})
