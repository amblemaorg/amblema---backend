# app/services/peca_initial_workshop_service.py

from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.models.peca_initial_workshop_model import InitialWorkshopPeca
from app.schemas.peca_initial_workshop_schema import InitialWorkshopPecaSchema
from app.helpers.error_helpers import RegisterNotFound
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.handler_images import upload_image
from app.helpers.document_metadata import getFileFields


class InitialWorkshopService():

    filesPath = 'initial_workshop'

    def get(self, pecaId, lapse):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            schema = InitialWorkshopPecaSchema()
            initialWorkshop = peca['lapse{}'.format(
                lapse)].initialWorkshop
            return schema.dump(initialWorkshop), 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def save(self, pecaId, lapse, jsonData, files=None):

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            try:
                schema = InitialWorkshopPecaSchema()

                if not peca['lapse{}'.format(lapse)].initialWorkshop:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"initialWorkshop lapse: ": lapse})
                if 'images' in jsonData:
                    self.filesPath = "school_years/{}/pecas/{}/{}".format(
                        peca.schoolYear.pk,
                        peca.pk,
                        self.filesPath
                    )
                    for image in jsonData['images']:
                        if str(image['image']).startswith('data'):
                            image['image'] = upload_image(
                                image['image'], self.filesPath, None)

                data = schema.load(jsonData)

                initialWorkshop = peca['lapse{}'.format(
                    lapse)].initialWorkshop

                for field in schema.dump(data).keys():
                    initialWorkshop[field] = data[field]
                try:
                    peca['lapse{}'.format(
                        lapse)].initialWorkshop = initialWorkshop
                    peca.save()
                    return schema.dump(initialWorkshop), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})
