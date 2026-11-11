# -*- coding: utf-8 -*-
# app/schemas/vademecum/admin_schema.py
"""Validación de los payloads de administración del backoffice (API-12, GES-03)."""

import re

from marshmallow import ValidationError, fields

from app.helpers.ma_schema_validators import Length, OneOf, Range, not_blank
from app.models.vademecum.constants import ACTIVE_STATUSES, GRADES, HEX_COLOR_REGEX
from app.schemas.vademecum.auth_schema import _Strict as StrictSchema

STATUS = OneOf(ACTIVE_STATUSES)
GRADE = OneOf(GRADES)


def _pattern(regex, msg):
    compiled = re.compile(regex)

    def validate(value):
        if value and not compiled.match(value):
            raise ValidationError({"status": "1", "msg": msg})
    return validate


CODE = _pattern(r"^[A-Za-z0-9]{1,4}$", "Invalid code")
COLOR = _pattern(HEX_COLOR_REGEX, "Invalid color")


class SeriesInputSchema(StrictSchema):
    id = fields.Str(load_default=None, allow_none=True)
    name = fields.Str(required=True, validate=(not_blank, Length(max=60)))
    code = fields.Str(required=True, validate=(not_blank, CODE))
    grades = fields.List(fields.Str(validate=GRADE), required=True)
    sort = fields.Int(load_default=0)


class SheetTypeInputSchema(StrictSchema):
    name = fields.Str(required=True, validate=(not_blank, Length(max=60)))
    headerName = fields.Str(required=True, validate=(not_blank, Length(max=60)))
    codePrefix = fields.Str(required=True, validate=(not_blank, CODE))
    color = fields.Str(required=True, validate=COLOR)
    sectionTitle = fields.Str(load_default=None, allow_none=True, validate=Length(max=150))
    sectionText = fields.Str(load_default=None, allow_none=True, validate=Length(max=5000))
    sort = fields.Int(required=True)
    status = fields.Str(load_default="1", validate=STATUS)
    series = fields.List(fields.Nested(SeriesInputSchema), load_default=list)


class AreaInputSchema(StrictSchema):
    name = fields.Str(required=True, validate=(not_blank, Length(max=80)))
    sort = fields.Int(required=True)
    status = fields.Str(load_default="1", validate=STATUS)


class SheetInputSchema(StrictSchema):
    """Edición parcial: solo se cambian los campos enviados."""
    number = fields.Int(validate=Range(min=1, max=999))
    title = fields.Str(validate=(not_blank, Length(max=150)))
    description = fields.Str(allow_none=True, validate=Length(max=2000))
    grades = fields.List(fields.Str(validate=GRADE))
    areaIds = fields.List(fields.Str())
    sheetTypeId = fields.Str(validate=not_blank)
    seriesId = fields.Str(allow_none=True)


class SiteContentInputSchema(StrictSchema):
    title = fields.Str(load_default=None, allow_none=True, validate=Length(max=150))
    body = fields.Str(load_default=None, allow_none=True, validate=Length(max=20000))


class SheetIdsSchema(StrictSchema):
    sheetIds = fields.List(fields.Str(), required=True, validate=Length(min=1, max=200))


class SheetCreateSchema(StrictSchema):
    """Datos de una ficha nueva subida desde el backoffice (API-11 rehecho)."""
    number = fields.Int(required=True, validate=Range(min=1, max=999))
    title = fields.Str(required=True, validate=(not_blank, Length(max=150)))
    sheetTypeId = fields.Str(required=True, validate=not_blank)
    seriesId = fields.Str(load_default=None, allow_none=True)
    description = fields.Str(load_default=None, allow_none=True, validate=Length(max=2000))
    grades = fields.List(fields.Str(validate=GRADE), load_default=list)
    areaIds = fields.List(fields.Str(), load_default=list)
