from mongoengine import Document, EmbeddedDocument, fields

class ActivityModel(EmbeddedDocument):
  name = fields.StringField(default='')
  printOption = fields.BooleanField(db_field='print', default=True)
  expandGallery = fields.BooleanField(default=True)
  lapse = fields.StringField(default='')

class SectionModel(EmbeddedDocument):
  name = fields.StringField(default='')
  printOption = fields.BooleanField(db_field='print', default=True)

class PecaProjectPrintOptionModel(Document):
  id_peca = fields.StringField(required=True)
  index = fields.BooleanField(default=True)
  activitiesPrint = fields.EmbeddedDocumentListField(ActivityModel)
  sectionsPrint = fields.EmbeddedDocumentListField(SectionModel)
  diagnosticPrint = fields.BooleanField(default=True)
  groupedGradesPrint = fields.ListField(fields.StringField(), default=list)