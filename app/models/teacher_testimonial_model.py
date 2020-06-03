# app/models/teacher_testimonial_model.py


from datetime import datetime
from bson import ObjectId

from flask import current_app
from mongoengine import fields, Document
from app.models.peca_project_model import Teacher


class TeacherTestimonial(Document):
    teacher = fields.ReferenceField(Teacher)
    image = fields.URLField(null=True)
    function = fields.StringField()
    description = fields.StringField()
    # stattus = ("1": "pending", "2": "approved", "3": "rejected")
    status = fields.StringField(default='1', max_length=1)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)