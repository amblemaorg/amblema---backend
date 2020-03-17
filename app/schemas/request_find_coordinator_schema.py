# app/schemas/request_find_coordinator_schema.py


from app.models.project_model import Project
from app.schemas.coordinator_contact_schema import CoordinatorContactSchema
from app.helpers.ma_schema_fields import MAReferenceField


class ReqFindCoordSchema(CoordinatorContactSchema):
    project = MAReferenceField(required=True, document=Project, field="code")
