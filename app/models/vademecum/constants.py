# -*- coding: utf-8 -*-
# app/models/vademecum/constants.py
"""Valores fijos del módulo Vademécum (ver Vademecum/docs/GES-02)."""

# Mismos valores que Section.grade ("0" = preescolar) más "all" para las fichas de todos los grados
GRADES = ("0", "1", "2", "3", "4", "5", "6", "all")
GRADE_LABELS = {
    "0": u"Preescolar",
    "1": u"1.º",
    "2": u"2.º",
    "3": u"3.º",
    "4": u"4.º",
    "5": u"5.º",
    "6": u"6.º",
    "all": u"Todos",
}

# "1" activo, "2" inactivo (convención del backend)
ACTIVE_STATUSES = ("1", "2")
SHEET_STATUSES = ("draft", "published", "unpublished")
# "pending" = sin verificar ni contraseña; "1" activa; "2" bloqueada por AmbLeMa
ACCOUNT_STATUSES = ("pending", "1", "2")
REQUEST_STATUSES = ("pending", "approved", "rejected")
COMMENT_STATUSES = ("pending", "approved", "hidden")
ORIGINS = ("enrollment", "external")

HEX_COLOR_REGEX = r"^#[0-9A-Fa-f]{6}$"

# Índice único que ignora los registros con borrado lógico
NOT_DELETED = {"isDeleted": False}
