# /app/blueprints/web_content/coordinator_page_model.py


from mongoengine import (
    EmbeddedDocument,
    StringField,
    ListField,
    EmbeddedDocumentListField)
from marshmallow import Schema, fields, post_load, EXCLUDE

from app.helpers.ma_schema_validators import not_blank, validate_image
from app.helpers.ma_schema_fields import MAImageField
from app.blueprints.web_content.models.templates_model import (
    Testimonial, TestimonialSchema)


class CoordinatorPage(EmbeddedDocument):
    backgroundImage = StringField(required=True)
    testimonials = EmbeddedDocumentListField(Testimonial, required=True)
    steps = ListField(StringField(), required=True)


"""
SCHEMAS FOR MODELS 
"""


class CoordinatorPageSchema(Schema):
    backgroundImage = MAImageField(
        required=True,
        validate=(not_blank, validate_image),
        folder='webcontent')
    testimonials = fields.List(fields.Nested(
        TestimonialSchema), required=True, validate=not_blank)
    steps = fields.List(fields.String(validate=not_blank))

    @post_load
    def make_document(self, data, **kwargs):
        return CoordinatorPage(**data)

    class Meta:
        unknown = EXCLUDE
