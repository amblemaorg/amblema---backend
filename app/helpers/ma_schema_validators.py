# app/helpers/ma_schema_validators.py


from marshmallow import ValidationError


def not_blank(data):
    """Custom marshmallow validator for empty string data
    """
    if not data:
        raise ValidationError("Field can't be blank")