# /app/blueprints/web_content/home_page_model.py


from mongoengine import (
    Document,
    StringField,
    BooleanField,
    EmbeddedDocumentField,
    EmbeddedDocumentListField)
from marshmallow import Schema, fields, pre_load, post_load

from app.helpers.ma_schema_validators import not_blank
from app.blueprints.web_content.models.home_page_model import (
    HomePage, HomePageSchema)

class WebContent(Document):
    homePage = EmbeddedDocumentField(HomePage, required=True)
    status = BooleanField(default=True)


"""
SCHEMAS FOR MODELS 
"""

class WebContentSchema(Schema):
    homePage = fields.Nested(HomePageSchema, required=True, validate=not_blank)
    
