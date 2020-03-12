# app/helpers/handler_images.py


from mimetypes import guess_extension, guess_type
from bson.objectid import ObjectId

from flask import current_app

from resources.images import path_images
from app.helpers.handler_files import upload
from app.helpers.error_helpers import CSTM_Exception


def upload_image(imageBase64, folder):
    """Method that save an image from a base64 string  
    Params:
      imageBase64: string  
      folder: string, folder into resource/images
    """
    # try:
    validExtensions = [".jpe", ".jpg", ".jpeg", ".png", ".svg"]
    ext = guess_extension(guess_type(imageBase64)[0])

    if ext in validExtensions:
        imageBase64 = imageBase64.replace(" ", "+")
        if ext in [".jpe", ".jpeg"]:
            ext = '.jpg'
            dataImage = imageBase64.lstrip('data:image/jpeg;base64')
        elif ext == ".png":
            dataImage = imageBase64.lstrip('data:image/png;base64')
        else:
            dataImage = imageBase64.lstrip('data:image/svg+xml;base64')
        pathImage = path_images + '/' + folder + '/'
        nameImage = str(ObjectId())
        urlImage = '/resources/images/' + folder + '/' + nameImage + ext

        upload(dataImage, nameImage, pathImage, ext)

        return current_app.config.get('SERVER_URL') + urlImage

    else:
        raise CSTM_Exception(message="Invalid image format",
                             status_code=400)

    # except Exception as e:
    #    current_app.logger.info(e)
    #    raise CSTM_Exception(message="An error ocurred on uploading image",
    #                         status_code=400,
    #                         payload={"error": str(e)})
