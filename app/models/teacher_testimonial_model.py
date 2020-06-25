# app/models/teacher_testimonial_model.py


from datetime import datetime
from bson import ObjectId

from flask import current_app
from mongoengine import fields, EmbeddedDocument


class TeacherTestimonial(EmbeddedDocument):
    id = fields.ObjectIdField(default=fields.ObjectId)
    teacherId = fields.StringField(required=True)
    firstName = fields.StringField(required=True)
    lastName = fields.StringField(required=True)
    image = fields.StringField()
    function = fields.StringField(required=True)
    description = fields.StringField(required=True)
    # approvalStatus = ("1": "pending", "2": "approved", "3": "rejected", "4": "cancelled")
    approvalStatus = fields.StringField(default='1', max_length=1)
    # visibilityStatus = ("1": "active", "2": "inactive")
    visibilityStatus = fields.StringField(default='1', max_length=1)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
