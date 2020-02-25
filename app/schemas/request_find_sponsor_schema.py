# app/schemas/request_find_sponsor_schema.py


from app.models.request_find_sponsor_model import Project
from app.schemas.sponsor_contact_schema import SponsorContactSchema
from app.helpers.ma_schema_fields import MAReferenceField


class ReqFindSponsorSchema(SponsorContactSchema):
    project = MAReferenceField(required=True, document=Project, field="code")
