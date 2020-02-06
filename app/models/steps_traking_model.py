# app/models/steps_tracking_model.py


from datetime import datetime
import json
from flask import current_app

from mongoengine import (
    Document,
    StringField,
    FloatField,
    URLField,
    BooleanField,
    DateTimeField,
    EmbeddedDocument,
    EmbeddedDocumentField,
    ReferenceField,
    LazyReferenceField)
from marshmallow import (
    Schema,
    fields,
    pre_load,
    post_load,
    EXCLUDE,
    validate,
    validates_schema,
    ValidationError)

from app.helpers.ma_schema_validators import not_blank
from app.helpers.ma_schema_fields import MAReferenceField
from app.helpers.error_helpers import RegisterNotFound
from app.services.generic_service import getRecordOr404
from app.models.user_model import SchoolUser, SponsorUser, CoordinatorUser


class StepsTracking(Document):
    name = StringField()
    schoolUser = ReferenceField('SchoolUser')
    sponsorUser = ReferenceField('SponsorUser')
    coordinatorUser = ReferenceField('CoordinatorUser')
    schoolYear = LazyReferenceField('SchoolYear', required=True)
    generalProgress = FloatField(default=0)
    schoolProgress = FloatField(default=0)
    sponsorProgress = FloatField(default=0)
    coordinatorProgress = FloatField(default=0)
    state = StringField(max_length=1, default='1')
    status = BooleanField(default=True)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'steps_trackings'}

    def clean(self):
        self.updatedAt = datetime.utcnow()
    
"""
SCHEMAS
"""


class StepsTrackingSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)
    schoolUser = MAReferenceField(field='name', dump_only=True)
    sponsorUser = MAReferenceField(field='firstName', dump_only=True)
    coordinatorUser = MAReferenceField(field='firstName', dump_only=True)
    generalProgress = fields.Str(dump_only=True)
    schoolProgress = fields.Str(dump_only=True)
    sponsorProgress = fields.Str(dump_only=True)
    coordinatorProgress = fields.Str(dump_only=True)
    state = fields.Str(
        validate=validate.OneOf(
            ('1','2','3'),
            ('in_progress','finished','discarded')
        ),
        dump_only=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)
    
    class Meta:
        unknown = EXCLUDE
        ordered = True