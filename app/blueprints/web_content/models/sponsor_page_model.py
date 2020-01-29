# /app/blueprints/web_content/sponsor_page_model.py


from mongoengine import (
    EmbeddedDocument,
    StringField,
    ListField,
    EmbeddedDocumentListField)
from marshmallow import Schema, fields, pre_load, post_load, EXCLUDE

from app.helpers.ma_schema_validators import not_blank, validate_image
from app.helpers.ma_schema_fields import MAImageField
from app.blueprints.web_content.models.templates_model import (
    Testimonial, TestimonialSchema)

class SponsorPage(EmbeddedDocument):
    backgroundImage = StringField(required=True)
    testimonials = EmbeddedDocumentListField(Testimonial, required=True)
    steps = ListField(StringField(), required=True)


"""
SCHEMAS FOR MODELS 
"""

class SponsorPageSchema(Schema):
    backgroundImage = MAImageField(required=True, validate=(not_blank, validate_image))
    testimonials= fields.List(fields.Nested(TestimonialSchema), required=True, validate=not_blank)
    steps = fields.List(fields.String(validate=not_blank))

    @post_load
    def make_document(self, data, **kwargs):
        return SponsorPage(**data)

    class Meta:
        unknown = EXCLUDE