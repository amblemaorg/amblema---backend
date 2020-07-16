# /app/blueprints/web_content/templates_model.py


from mongoengine import (
    EmbeddedDocument,
    StringField,
    EmbeddedDocumentField)
from marshmallow import Schema, fields, post_load

from app.helpers.ma_schema_validators import not_blank, validate_image, Length
from app.helpers.ma_schema_fields import MAImageField


class Background(EmbeddedDocument):
    image = StringField(required=True)
    description = StringField()


class Multimedia(EmbeddedDocument):
    url = StringField(required=True)
    type = StringField(required=True)


class Testimonial(EmbeddedDocument):
    firstName = StringField(required=True)
    lastName = StringField(required=True)
    image = StringField(required=True)
    function = StringField()
    description = StringField(required=True)


"""
SCHEMAS FOR MODELS 
"""


class BackgroundSchema(Schema):
    image = MAImageField(
        required=True,
        validate=(not_blank, validate_image),
        folder='webcontent',
        size="339")
    description = fields.Str(validate=(
        Length(max=54)
    ))

    @post_load
    def make_document(self, data, **kwargs):
        return Background(**data)


class TestimonialSchema(Schema):
    firstName = fields.Str(required=True, validate=not_blank)
    lastName = fields.Str(required=True, validate=not_blank)
    image = MAImageField(
        required=True,
        validate=(not_blank, validate_image),
        folder='webcontent',
        size=20)
    function = fields.Str(required=True, validate=not_blank)
    description = fields.Str(
        required=True, validate=(not_blank, Length(max=322)))

    @post_load
    def make_document(self, data, **kwargs):
        return Testimonial(**data)
