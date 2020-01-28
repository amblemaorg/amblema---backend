# /app/blueprints/web_content/home_page_model.py


from mongoengine import (
    EmbeddedDocument,
    StringField,
    EmbeddedDocumentField,
    EmbeddedDocumentListField)
from marshmallow import Schema, fields, pre_load, post_load, EXCLUDE

from app.helpers.ma_schema_validators import not_blank
from app.blueprints.web_content.models.templates_model import (
    Slider, SliderSchema, Testimonial, TestimonialSchema)

class HomePage(EmbeddedDocument):
    sliders = EmbeddedDocumentListField(Slider, required=True)
    aboutUsText = StringField(required=True)
    environmentText = StringField(required=True)
    readingText = StringField(required=True)
    mathText = StringField(required=True)
    testimonials = EmbeddedDocumentListField(Testimonial, required=True)


"""
SCHEMAS FOR MODELS 
"""

class HomePageSchema(Schema):
    sliders = fields.List(fields.Nested(SliderSchema), required=True, validate=not_blank)
    aboutUsText = fields.Str(required=True, validate=not_blank)
    environmentText = fields.Str(required=True, validate=not_blank)
    readingText = fields.Str(required=True, validate=not_blank)
    mathText = fields.Str(required=True, validate=not_blank)
    testimonials= fields.List(fields.Nested(TestimonialSchema), required=True, validate=not_blank)

    @post_load
    def make_document(self, data, **kwargs):
        return HomePage(**data)

    class Meta:
        unknown = EXCLUDE