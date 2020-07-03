# app/models/teacher_testimonial_model.py


from datetime import datetime
from bson import ObjectId

from flask import current_app
from mongoengine import fields, EmbeddedDocument
from app.models.shared_embedded_documents import Approval


class Testimonial(EmbeddedDocument):
    teacherId = fields.StringField(required=True)
    firstName = fields.StringField(required=True)
    lastName = fields.StringField(required=True)
    image = fields.StringField()
    position = fields.StringField(required=True)
    description = fields.StringField(required=True)


class TeacherTestimonial(EmbeddedDocument):
    approvalStatus = fields.StringField(default='1', max_length=1)
    testimonials = fields.EmbeddedDocumentListField(Testimonial, max_length=4)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    approvalHistory = fields.EmbeddedDocumentListField(Approval)
    isInApproval = fields.BooleanField(default=False)
