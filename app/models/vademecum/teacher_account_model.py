# -*- coding: utf-8 -*-
# app/models/vademecum/teacher_account_model.py

import hashlib
from datetime import datetime

from flask_bcrypt import Bcrypt
from mongoengine import Document, EmbeddedDocument, fields

from app.models.vademecum.constants import ACCOUNT_STATUSES


def hash_token(raw):
    """SHA-256 hex of an email token; only the hash is stored, never the token."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class AccountToken(EmbeddedDocument):
    tokenHash = fields.StringField(required=True)
    expiresAt = fields.DateTimeField(required=True)
    usedAt = fields.DateTimeField(null=True)


class VademecumTeacherAccount(Document):
    """Cuenta del portal, separada de `users` (no comparte secreto JWT ni roles)."""
    email = fields.EmailField(required=True)
    # Vacía mientras la cuenta está "pending": se crea desde el enlace del correo
    password = fields.StringField(null=True)
    firstName = fields.StringField(required=True)
    lastName = fields.StringField(required=True)
    status = fields.StringField(choices=ACCOUNT_STATUSES, default="pending")
    emailVerifiedAt = fields.DateTimeField(null=True)
    emailVerification = fields.EmbeddedDocumentField(AccountToken, null=True)
    passwordReset = fields.EmbeddedDocumentField(AccountToken, null=True)
    # Tokens JWT emitidos antes de esta fecha dejan de valer
    passwordChangedAt = fields.DateTimeField(null=True)
    lastLoginAt = fields.DateTimeField(null=True)
    isDeleted = fields.BooleanField(default=False)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {
        "collection": "vademecum_teacher_accounts",
        "indexes": [
            {"fields": ["email"], "unique": True},
            "emailVerification.tokenHash",
            "passwordReset.tokenHash",
        ],
    }

    def clean(self):
        self.updatedAt = datetime.utcnow()
        if self.email:
            self.email = self.email.lower().strip()

    def set_password(self, raw):
        self.password = Bcrypt().generate_password_hash(raw).decode()
        self.passwordChangedAt = datetime.utcnow()

    def password_is_valid(self, raw):
        if not self.password:
            return False
        return Bcrypt().check_password_hash(self.password, raw)
