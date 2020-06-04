# app/models/teacher_testimonial_model.py


from datetime import datetime
from bson import ObjectId

from flask import current_app
from mongoengine import fields, EmbeddedDocument
from app.models.peca_project_model import Teacher


class TeacherTestimonial(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    teacher = fields.ReferenceField(Teacher)
    firstName = StringField(required=True)
    lastName = StringField(required=True)
    image = fields.URLField(required=True)
    function = fields.StringField(required=True)
    description = fields.StringField(required=True)
    # stattus = ("1": "pending", "2": "approved", "3": "rejected")
    status = fields.StringField(default='1', max_length=1)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)