# /app/blueprints/web_content/about_us_page_model.py


from mongoengine import (
    EmbeddedDocument,
    StringField,
    EmbeddedDocumentField,
    EmbeddedDocumentListField)
from marshmallow import Schema, fields, pre_load, post_load, EXCLUDE

from app.helpers.ma_schema_validators import not_blank, validate_image
from app.helpers.ma_schema_fields import MAImageField
from app.blueprints.web_content.models.templates_model import (
    Background, BackgroundSchema)

class Award(EmbeddedDocument):
    title = StringField(required=True)
    image = StringField(required=True)
    description = StringField(required=True)
    description2 = StringField(required=True)

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
    image = MAImageField(required=True, validate=(not_blank, validate_image))
    description = fields.Str(required=True, validate=not_blank)
    description2 = fields.Str(required=True, validate=not_blank)

    @post_load
    def make_document(self, data, **kwargs):
        return Award(**data)

class AboutUsPageSchema(Schema):
    slider = fields.List(fields.Nested(BackgroundSchema), required=True, validate=not_blank)
    aboutUsText = fields.Str(required=True, validate=not_blank)
    environmentText = fields.Str(required=True, validate=not_blank)
    readingText = fields.Str(required=True, validate=not_blank)
    mathText = fields.Str(required=True, validate=not_blank)
    awards= fields.List(fields.Nested(AwardSchema), required=True, validate=not_blank)

    @post_load
    def make_document(self, data, **kwargs):
        return AboutUsPage(**data)

    class Meta:
        unknown = EXCLUDE