# app/helpers/handler_images.py


import re

from bson.objectid import ObjectId

from resources.images import path_images
from app.helpers.error_helpers import CSTM_Exception
from marshmallow import ValidationError
from PIL import Image, ImageOps
import base64, io, os

from pathlib import Path

# Uploaded images are normalized before being stored: EXIF orientation applied,
# longest side limited and re-encoded. Yearbook PDFs embed them at 900px max.
IMAGE_MAX_SIDE = int(os.getenv('IMAGE_MAX_SIDE', 1920))
IMAGE_JPEG_QUALITY = int(os.getenv('IMAGE_JPEG_QUALITY', 82))

DATA_URL_RE = re.compile(r'^data:image/([a-zA-Z0-9.+-]+);base64,(.*)$', re.DOTALL)


def upload_image(imageBase64, folder, size=None, is_yearbook=False):
    """Method that save an image from a base64 string
    Params:
    imageBase64: string
    folder: string, folder into resource/images
    size: float, max image size in KB
    is_yearkbook: boolean
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
        try:
            match = DATA_URL_RE.match(imageBase64)
            if not match:
                raise ValueError('Invalid data URL')
            dataImage = base64.b64decode(match.group(2))

            # verify() detects truncated/corrupt files; the image must be reopened after it
            Image.open(io.BytesIO(dataImage)).verify()
            image = Image.open(io.BytesIO(dataImage))

            content, ext = optimize_image(image, dataImage)

            pathImage = path_images + '/' + folder + '/'
            Path(pathImage).mkdir(parents=True, exist_ok=True)
            nameImage = str(ObjectId())
            with open(pathImage + nameImage + ext, 'wb') as imageFile:
                imageFile.write(content)
            urlImage = '/resources/images/' + folder + '/' + nameImage + ext
        except Exception as e:
            if is_yearbook:
                return ''
            else:
                raise CSTM_Exception(message="Invalid image format",
                                        status_code=400)
        return urlImage
    else:
        raise CSTM_Exception(message="Invalid image format",
                            status_code=400)


def optimize_image(image, original):
    """Return (bytes, extension) of the image ready to be stored.
    Photos are saved as progressive JPEG; PNG with transparency or few colors
    (logos, graphics) stays PNG to avoid JPEG artifacts on edges.
    """
    sourceFormat = str(image.format).upper()

    # Animated GIFs would lose their frames: stored untouched
    if sourceFormat == 'GIF' and getattr(image, 'is_animated', False):
        return original, '.gif'

    hasExif = bool(image.info.get('exif'))
    transposed = image.getexif().get(0x0112, 1) != 1  # EXIF Orientation tag
    if transposed:
        image = ImageOps.exif_transpose(image)

    resized = max(image.size) > IMAGE_MAX_SIDE
    if resized:
        image.thumbnail((IMAGE_MAX_SIDE, IMAGE_MAX_SIDE), Image.LANCZOS)

    buffer = io.BytesIO()
    if is_graphic(image, sourceFormat):
        if image.mode not in ('RGBA', 'LA', 'RGB', 'L', 'P'):
            image = image.convert('RGBA')
        image.save(buffer, 'PNG', optimize=True)
        ext, sameFormat = '.png', sourceFormat == 'PNG'
    else:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(buffer, 'JPEG', quality=IMAGE_JPEG_QUALITY,
                   optimize=True, progressive=True)
        ext, sameFormat = '.jpeg', sourceFormat in ('JPEG', 'MPO')

    content = buffer.getvalue()
    # Already optimized source (e.g. compressed by the browser): re-encoding it
    # would only add generational loss. EXIF is never kept (may carry GPS data).
    if (sameFormat and not resized and not transposed and not hasExif
            and len(original) <= len(content)):
        return original, ext
    return content, ext


def is_graphic(image, sourceFormat):
    """True for images that must stay lossless: transparency or few colors"""
    if sourceFormat in ('JPEG', 'MPO') or image.mode in ('CMYK', 'YCbCr'):
        return False
    if image.mode in ('RGBA', 'LA') or (
            image.mode == 'P' and 'transparency' in image.info):
        if image.mode == 'P':
            image = image.convert('RGBA')
        if image.getchannel('A').getextrema()[0] < 255:
            return True
    # Logos and diagrams use few colors; photos exceed 256 quickly
    return image.getcolors(maxcolors=256) is not None


def get_size(b64string):
    return (len(b64string) * 3) / 4 - b64string.count('=', -2)
