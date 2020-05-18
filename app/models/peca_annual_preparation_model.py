# app/models/peca_annual_preparation_model.py

from datetime import datetime
from bson import ObjectId

from mongoengine import EmbeddedDocument, fields


class AnnualPreparationPeca(EmbeddedDocument):
    step1Description = fields.StringField()
    step2Description = fields.StringField()
    step3Description = fields.StringField()
    step4Description = fields.StringField()
