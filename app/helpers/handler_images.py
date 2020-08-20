# app/helpers/handler_images.py


from mimetypes import guess_extension, guess_type
from bson.objectid import ObjectId

from flask import current_app

from resources.images import path_images
from app.helpers.handler_files import upload
from app.helpers.error_helpers import CSTM_Exception
from marshmallow import ValidationError
from PIL import Image
import base64
import io
from pathlib import Path

def upload_image(imageBase64, folder, size=None):
    """Method that save an image from a base64 string  
    Params:
      imageBase64: string  
      folder: string, folder into resource/images
      size: float, max image size in KB
    """

    validExtensions = ["jpe", "jpg", "jpeg", "png", "svg"]

    imageBase64 = imageBase64.replace(" ", "+")

    endExt = imageBase64.index(';')
    ext = imageBase64[11:endExt]

    if ext in validExtensions:
        if size and get_size(imageBase64)/1024 > size:
            raise ValidationError(
                {
                    "status": "13",
                    "msg": "Invalid image size. Max allowed {} KB".format(size)
                }
            )
        dataImage = imageBase64.lstrip(
                'data:image/{};base64'.format(ext))

        pathImage = path_images + '/' + folder + '/'
        Path(pathImage).mkdir(parents=True, exist_ok=True)
        nameImage = str(ObjectId())

        dataImage = base64.b64decode(dataImage)
        image = Image.open(io.BytesIO(dataImage))
        ext = '.{}'.format(str(image.format).lower())
        image.save(pathImage+nameImage+ext, image.format)
        urlImage = '/resources/images/' + folder + '/' + nameImage + ext
        return urlImage

    else:
        raise CSTM_Exception(message="Invalid image format",
                             status_code=400)


def get_size(b64string):
    return (len(b64string) * 3) / 4 - b64string.count('=', -2)
