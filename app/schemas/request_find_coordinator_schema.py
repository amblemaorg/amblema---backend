# app/schemas/request_find_coordinator_schema.py


from app.models.user_model import User
from app.models.project_model import Project
from app.schemas.coordinator_contact_schema import CoordinatorContactSchema
from app.helpers.ma_schema_fields import MAReferenceField
from app.schemas import fields


class ReqFindCoordSchema(CoordinatorContactSchema):
    user = MAReferenceField(required=True, document=User, field="name")
    project = MAReferenceField(required=True, document=Project, field="code")
    isReferred = fields.Bool(dump_only=True)
    referredName = fields.Str(dump_only=True)
