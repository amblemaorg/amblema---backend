# /app/blueprints/web_content/home_page_model.py


from mongoengine import (
    EmbeddedDocument,
    StringField,
    IntField,
    EmbeddedDocumentField,
    EmbeddedDocumentListField)
from marshmallow import Schema, fields, post_load, EXCLUDE

from app.helpers.ma_schema_validators import not_blank, Length
from app.blueprints.web_content.models.templates_model import (
    Background, BackgroundSchema, Testimonial, TestimonialSchema)


class HomePage(EmbeddedDocument):
    slider = EmbeddedDocumentListField(Background, required=True)
    aboutUsText = StringField(required=True)
    environmentText = StringField(required=True)
    readingText = StringField(required=True)
    mathText = StringField(required=True)
    testimonials = EmbeddedDocumentListField(Testimonial, required=True)


"""
SCHEMAS FOR MODELS 
"""


class HomePageSchema(Schema):
    slider = fields.List(fields.Nested(BackgroundSchema),
                         required=True, validate=not_blank)
    aboutUsText = fields.Str(
        required=True, validate=(not_blank, Length(max=317)))
    environmentText = fields.Str(
        required=True, validate=(not_blank, Length(max=313)))
    readingText = fields.Str(
        required=True, validate=(not_blank, Length(max=313)))
    mathText = fields.Str(required=True, validate=(not_blank, Length(max=313)))
    testimonials = fields.List(fields.Nested(
        TestimonialSchema), required=True, validate=not_blank)

    @post_load
    def make_document(self, data, **kwargs):
        return HomePage(**data)

    class Meta:
        unknown = EXCLUDE
