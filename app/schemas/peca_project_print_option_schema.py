from marshmallow import (
    Schema,
    pre_load,
    post_load,
    EXCLUDE,
    validate,
    validates_schema,
    ValidationError)
from app.schemas import fields
from flask import current_app

class ActivitySchema(Schema):
  name = fields.Str(allow_none=True) 
  print = fields.Bool()
  expandGallery = fields.Bool()
  lapse = fields.Str()

class SectionSchema(Schema):
  name = fields.Str()
  print = fields.Bool()

class PecaProjectPrintOption(Schema):
  id_peca = fields.Str(required=True)
  index = fields.Bool()
  activitiesPrint = fields.List(fields.Nested(ActivitySchema))
  sectionsPrint = fields.List(fields.Nested(SectionSchema))
  diagnosticPrint = fields.Bool()