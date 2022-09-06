from email.policy import default
from unicodedata import name
from mongoengine import Document, EmbeddedDocument, fields
from flask import current_app

class ActivityModel(EmbeddedDocument):
  name = fields.StringField(default='')
  print = fields.BooleanField(default=True)
  expandGallery = fields.BooleanField(default=True)
  lapse = fields.StringField(default='')

class SectionModel(EmbeddedDocument):
  name = fields.StringField(default='')
  print = fields.BooleanField(default=True)

class PecaProjectPrintOptionModel(Document):
  id_peca = fields.StringField(required=True)
  index = fields.BooleanField(default=True)
  activitiesPrint = fields.EmbeddedDocumentListField(ActivityModel)
  sectionsPrint = fields.EmbeddedDocumentListField(SectionModel)
  diagnosticPrint = fields.BooleanField(default=True)