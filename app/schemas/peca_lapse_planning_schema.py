# app/schemas/peca_lapse_planning_schema.py


from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank, OneOf
from app.schemas.shared_schemas import FileSchema, ReferenceSchema, ApprovalSchema
from app.models.peca_olympics_model import Section


class LapsePlanningPecaSchema(Schema):
    name = fields.Str(dump_only=True)
    proposalFundationFile = fields.Nested(FileSchema(), dump_only=True)
    proposalFundationDescription = fields.Str(dump_only=True)
    meetingDescription = fields.Str(dump_only=True)
    isStandard = fields.Bool(dump_only=True)
    attachedFile = fields.Nested(FileSchema())
    meetingDate = fields.DateTime()
    isInApproval = fields.Boolean(dump_only=True)
    approvalHistory = fields.List(
        fields.Nested(ApprovalSchema), dump_only=True)
    status = fields.Str(
        validate=(
            OneOf(
                ["1", "2"],
                ["pending", "approved", ]
            )))

    class Meta:
        unknown = EXCLUDE
        ordered = True
