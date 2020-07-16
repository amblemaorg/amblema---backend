# /app/blueprints/web_content/sponsor_page_model.py


from mongoengine import (
    EmbeddedDocument,
    StringField,
    URLField,
    IntField,
    ListField,
    EmbeddedDocumentListField)
from marshmallow import Schema, fields, post_load, EXCLUDE

from app.helpers.ma_schema_validators import not_blank, validate_image, validate_url, Length
from app.helpers.ma_schema_fields import MAImageField
from app.blueprints.web_content.models.templates_model import (
    Testimonial)


class Sponsor(EmbeddedDocument):
    id = StringField()
    name = StringField()
    image = StringField()
    webSite = URLField()
    position = IntField()


class SponsorPage(EmbeddedDocument):
    backgroundImage = StringField(required=True)
    testimonials = EmbeddedDocumentListField(Testimonial, required=True)
    steps = ListField(StringField(), required=True)
    sponsors = EmbeddedDocumentListField(Sponsor)


"""
SCHEMAS FOR MODELS
"""


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
        required=True, validate=(not_blank, Length(max=197)))

    @post_load
    def make_document(self, data, **kwargs):
        return Testimonial(**data)


class SponsorSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    image = MAImageField(validate=(validate_image))
    webSite = fields.Str(validate=(validate_url))
    position = fields.Int()

    @post_load
    def make_document(self, data, **kwargs):
        return Sponsor(**data)


class SponsorPageSchema(Schema):
    backgroundImage = MAImageField(
        required=True,
        validate=(not_blank, validate_image),
        folder='webcontent')
    testimonials = fields.List(fields.Nested(
        TestimonialSchema), required=True, validate=not_blank)
    steps = fields.List(fields.String(validate=(not_blank, Length(max=231))))
    sponsors = fields.List(fields.Nested(SponsorSchema))

    @post_load
    def make_document(self, data, **kwargs):
        return SponsorPage(**data)

    class Meta:
        unknown = EXCLUDE
