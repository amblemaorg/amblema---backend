# -*- coding: utf-8 -*-
# app/models/vademecum/rating_model.py

from datetime import datetime

from mongoengine import Document, fields

from app.models.vademecum.constants import COMMENT_STATUSES


class VademecumRating(Document):
    """Una valoración por cuenta y ficha, editable. Las estrellas no pasan por moderación."""
    account = fields.ReferenceField("VademecumTeacherAccount", required=True)
    sheet = fields.ReferenceField("VademecumSheet", required=True)
    stars = fields.IntField(required=True, min_value=1, max_value=5)
    comment = fields.StringField(null=True)
    commentStatus = fields.StringField(choices=COMMENT_STATUSES, null=True)
    moderatedBy = fields.ReferenceField("User", null=True)
    moderatedAt = fields.DateTimeField(null=True)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {
        "collection": "vademecum_ratings",
        "indexes": [
            {"fields": ["account", "sheet"], "unique": True},
            ("sheet", "commentStatus", "-updatedAt"),
            ("commentStatus", "-updatedAt"),
        ],
    }

    def clean(self):
        self.updatedAt = datetime.utcnow()

    def set_comment(self, text):
        """A changed comment goes back to moderation; an empty one removes it."""
        text = (text or u"").strip() or None
        if text is None:
            self.comment = None
            self.commentStatus = None
        elif text != self.comment:
            self.comment = text
            self.commentStatus = "pending"
        else:
            return
        self.moderatedBy = None
        self.moderatedAt = None
