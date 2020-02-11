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
from app.blueprints.web_content.models.about_us_page_model import (
    AboutUsPage, AboutUsPageSchema
)
from app.blueprints.web_content.models.sponsor_page_model import (
    SponsorPage, SponsorPageSchema
)
from app.blueprints.web_content.models.coordinator_page_model import (
    CoordinatorPage, CoordinatorPageSchema
)

class WebContent(Document):
    homePage = EmbeddedDocumentField(HomePage)
    aboutUsPage = EmbeddedDocumentField(AboutUsPage)
    sponsorPage = EmbeddedDocumentField(SponsorPage)
    coordinatorPage = EmbeddedDocumentField(CoordinatorPage)


"""
SCHEMAS FOR MODELS 
"""

class WebContentSchema(Schema):
    homePage = fields.Nested(HomePageSchema, required=True, validate=not_blank)
    aboutUsPage = fields.Nested(AboutUsPageSchema, required=True, validate=not_blank)
    sponsorPage = fields.Nested(SponsorPageSchema, required=True, validate=not_blank)
    coordinatorPage = fields.Nested(CoordinatorPageSchema, required=True, validate=not_blank)
    
