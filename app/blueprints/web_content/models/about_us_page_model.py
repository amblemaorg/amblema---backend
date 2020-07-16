# /app/blueprints/web_content/models/about_us_page_model.py


from mongoengine import (
    EmbeddedDocument,
    StringField,
    EmbeddedDocumentField,
    EmbeddedDocumentListField)
from marshmallow import Schema, fields, post_load, EXCLUDE

from app.helpers.ma_schema_validators import not_blank, validate_image, Length
from app.helpers.ma_schema_fields import MAImageField
from app.blueprints.web_content.models.templates_model import (
    Background, BackgroundSchema)


class Award(EmbeddedDocument):
    title = StringField(required=True)
    image = StringField(required=True)
    image2 = StringField(required=True)
    image3 = StringField(required=True)
    description = StringField(required=True)
    description2 = StringField()


class AboutUsPage(EmbeddedDocument):
    slider = EmbeddedDocumentListField(Background, required=True)
    aboutUsText = StringField(required=True)
    environmentText = StringField(required=True)
    readingText = StringField(required=True)
    mathText = StringField(required=True)
    awards = EmbeddedDocumentListField(Award, required=True)


"""
SCHEMAS FOR MODELS 
"""


class AwardSchema(Schema):
    title = fields.Str(required=True, validate=not_blank)
    image = MAImageField(
        required=True,
        validate=(not_blank, validate_image),
        folder='webcontent')
    image2 = MAImageField(
        required=True,
        validate=(not_blank, validate_image),
        folder='webcontent')
    image3 = MAImageField(
        required=True,
        validate=(not_blank, validate_image),
        folder='webcontent')
    description = fields.Str(
        required=True, validate=(not_blank, Length(max=481)))
    description2 = fields.Str(validate=Length(max=403))

    @post_load
    def make_document(self, data, **kwargs):
        return Award(**data)


class AboutUsPageSchema(Schema):
    slider = fields.List(fields.Nested(BackgroundSchema),
                         required=True, validate=not_blank)
    aboutUsText = fields.Str(
        required=True, validate=(not_blank, Length(max=1728)))
    environmentText = fields.Str(
        required=True, validate=(not_blank, Length(max=579)))
    readingText = fields.Str(
        required=True, validate=(not_blank, Length(max=579)))
    mathText = fields.Str(required=True, validate=(not_blank, Length(max=579)))
    awards = fields.List(fields.Nested(AwardSchema),
                         required=True, validate=not_blank)

    @post_load
    def make_document(self, data, **kwargs):
        return AboutUsPage(**data)

    class Meta:
        unknown = EXCLUDE
