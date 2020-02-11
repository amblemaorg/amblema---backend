# /app/blueprints/web_content/templates_model.py


from mongoengine import (
    EmbeddedDocument,
    StringField,
    EmbeddedDocumentField)
from marshmallow import Schema, fields, pre_load, post_load

from app.helpers.ma_schema_validators import not_blank, validate_image
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
        folder='webcontent')
    description = fields.Str()

    @post_load
    def make_document(self, data, **kwargs):
        return Background(**data)


class TestimonialSchema(Schema):
    firstName = fields.Str(required=True, validate=not_blank)
    lastName = fields.Str(required=True, validate=not_blank)
    image = MAImageField(
        required=True,
        validate=(not_blank, validate_image),
        folder='webcontent')
    function = fields.Str(required=True, validate=not_blank)
    description = fields.Str(required=True, validate=not_blank)

    @post_load
    def make_document(self, data, **kwargs):
        return Testimonial(**data)
