# /app/blueprints/web_content/post_model.py


from datetime import datetime
from flask_mongoengine import Document
from mongoengine import (
    # Document,
    StringField,
    BooleanField,
    DateTimeField,
    URLField)
from marshmallow import Schema, post_load, EXCLUDE

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank, OneOf
from app.helpers.ma_schema_fields import MAImageField


class Post(Document):
    title = StringField(required=True)
    tag = StringField(max_length=1)
    image = StringField(required=True)
    image2 = StringField(required=True)
    text = StringField(required=True)
    status = StringField(max_length=1)
    isDeleted = BooleanField(default=False)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'posts'}

    def clean(self):
        self.updatedAt = datetime.utcnow()


"""
SCHEMAS FOR MODELS 
"""


class PostSchema(Schema):
    id = fields.Str(dump_only=True)
    title = fields.Str(required=True)
    tag = fields.Str(
        required=True,
        validate=OneOf(
            ('1', '2', '3', '4'),
            ('environment', 'reading', 'math', 'other')
        )
    )
    image = MAImageField(required=True, folder='posts')
    image2 = MAImageField(required=True, folder='posts')
    text = fields.Str(required=True)
    status = fields.Str(
        required=True,
        validate=OneOf(
            ('1', '2'),
            ('published', 'unpublished')
        )
    )
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True
