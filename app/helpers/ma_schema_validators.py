# app/helpers/ma_schema_validators.py


import mimetypes
from marshmallow import ValidationError
import re


def not_blank(data):
    """Custom marshmallow validator for empty string data
    """
    if not data:
        raise ValidationError("Field can't be blank")

def only_letters(data):
    """Custom marshmallow validator for only letters
    """
    if not re.match("^[a-zA-ZñÑáéíóúÁÉÍÓÚ ]*$", data):
        raise ValidationError("Field accepts only letters")

def only_numbers(data):
    """Custom marshmallow validator for only numbers
    """
    if not re.match("^[0-9]*$", data):
        raise ValidationError("Field accepts only numbers")

def validate_image(data):
    mimetype,encoding = mimetypes.guess_type(data)
    if not (mimetype and mimetype.startswith('image')):
        raise ValidationError("Invalid image url")

def validate_video(data):

    #mimetype,encoding = mimetypes.guess_type(data)
    #if not (mimetype and mimetype.startswith('video')):
    #    raise ValidationError("Invalid video url")
    return True