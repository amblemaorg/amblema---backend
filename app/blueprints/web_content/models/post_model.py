# /app/blueprints/web_content/post_model.py


from datetime import datetime

from mongoengine import (
    Document,
    StringField,
    BooleanField,
    DateTimeField,
    URLField)
from marshmallow import Schema, fields, post_load, EXCLUDE

from app.helpers.ma_schema_validators import not_blank
from app.helpers.ma_schema_fields import MAImageField


class Post(Document):
    image = URLField(required=True)
    image2 = URLField(required=True)
    text = StringField(required=True)
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
    image = MAImageField(required=True, folder='posts')
    image2 = MAImageField(required=True, folder='posts')
    text = fields.Str(required=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True
