# -*- coding: utf-8 -*-
# app/helpers/vademecum_seeds.py
"""Índices y semillas iniciales del módulo Vademécum (API-01).

Las semillas solo crean lo que falta y nunca actualizan lo existente: lo que el administrador
edite desde el backoffice no se pisa. Colores de HT/IM/MX y las áreas son provisionales
(DIS-01 y la lista de AmbLeMa en S2).
"""

from app.models.vademecum import (
    VADEMECUM_MODELS, VademecumDownload, VademecumSheet, VademecumSheetType, VademecumArea,
    VademecumSiteContent)

SHEET_TYPES = (
    dict(codePrefix="HT", name=u"Hora TAL", headerName=u"Hora TAL", color="#F2A93B", sort=1),
    dict(codePrefix="IM", name=u"Ingenio Matemático", headerName=u"Ingenio Matemático",
         color="#2F80ED", sort=2),
    dict(codePrefix="MX", name=u"Momento X", headerName=u"Momento X", color="#1F3A68", sort=3),
    # Los compendios de Ambiente se encabezan "Ecotema N: Título" (ficha) y "Juego N" (fichas
    # aparte); el backoffice reconoce ese formato por el encabezado "Ecotema"
    dict(codePrefix="AM", name=u"Ambiente", headerName=u"Ecotema", color="#94C021", sort=4),
)

# Áreas provisionales con los tipos a los que aplican (prefijos)
AREAS = (
    (u"Comprensión lectora", 1, ("HT",)),
    (u"Geometría", 2, ("IM", "MX")),
    (u"Operaciones matemáticas", 3, ("IM", "MX")),
    (u"Geografía", 4, ("AM",)),
)

SITE_CONTENT_KEYS = ("home", "about", "access_request")


def ensure_vademecum_indexes():
    """Creates the indexes declared in each Vademécum model; returns how many models."""
    from app.services.vademecum.enrollment_service import ensure_teacher_email_index
    for model in VADEMECUM_MODELS:
        model.ensure_indexes()
    # Índice sobre la colección users existente (aditivo): búsqueda de matrícula por email
    ensure_teacher_email_index()
    return len(VADEMECUM_MODELS)


def seed_vademecum():
    """Creates the missing seed records; returns what this run created."""
    created = {"sheetTypes": 0, "areas": 0, "siteContent": 0}

    # Un tipo borrado por el administrador cuenta como existente: no se resucita
    for data in SHEET_TYPES:
        if VademecumSheetType.objects(codePrefix=data["codePrefix"]).first():
            continue
        VademecumSheetType(**data).save()
        created["sheetTypes"] += 1

    # Áreas provisionales solo en una base sin áreas: renombrarlas o borrarlas no las recrea
    if VademecumArea.objects.count() == 0:
        types = {t.codePrefix: t for t in VademecumSheetType.objects(isDeleted=False)}
        for name, sort, prefixes in AREAS:
            VademecumArea(name=name, sort=sort,
                          sheetTypes=[types[p] for p in prefixes if p in types]).save()
            created["areas"] += 1

    for key in SITE_CONTENT_KEYS:
        if VademecumSiteContent.objects(key=key).first():
            continue
        VademecumSiteContent(key=key).save()
        created["siteContent"] += 1

    return created


# --- Áreas por tipo de ficha (2026-11-23) ---

def link_vademecum_area_types():
    """Áreas sin tipo de ficha (creadas antes de ligarlas): se les dan todos los tipos activos.

    Así nada deja de funcionar (una ficha solo acepta áreas de su tipo, código 121); después el
    administrador deja en cada área solo los tipos que le corresponden. Idempotente.
    Devuelve {"areas": [nombres actualizados], "sheetTypes": cuántos tipos se asignaron}.
    """
    types = list(VademecumSheetType.objects(isDeleted=False))
    updated = []
    for area in VademecumArea.objects(isDeleted=False):
        if not area.sheetTypes:
            area.sheetTypes = types
            area.save()
            updated.append(area.name)
    return {"areas": updated, "sheetTypes": len(types)}


# --- Retiro de las series (2026-11-23) ---

OLD_SHEET_INDEX_KEY = [("sheetType", 1), ("seriesId", 1), ("number", 1)]


def remove_vademecum_series():
    """Quita las series de una base creada antes de retirarlas. Idempotente.

    MongoEngine no carga documentos con campos que el modelo ya no declara (FieldDoesNotExist),
    así que hay que correrlo antes de usar Vademécum en una base con datos previos:
    - Borra `series` de los tipos, `seriesId` de las fichas y `sheet.seriesId` de las descargas.
    - Borra el índice único viejo (sheetType, seriesId, number) y crea los nuevos.
    - Recalcula el código de las fichas que lo tenían con serie (IM34-1 pasa a IM-1). Si dos
      fichas quedan con el mismo tipo y número, conservan su código, se informan en
      `conflicts` y no se crea el índice nuevo: hay que renumerarlas y volver a correrlo.
    Devuelve {"sheetTypes", "sheets", "downloads", "indexDropped", "codes", "conflicts"}.
    """
    from bson import SON
    from mongoengine.connection import get_db

    # Colecciones sin pasar por el modelo: _get_collection() crearía el índice nuevo antes de
    # poder informar fichas repetidas
    db = get_db()
    types = db[VademecumSheetType._meta["collection"]]
    sheets = db[VademecumSheet._meta["collection"]]
    downloads = db[VademecumDownload._meta["collection"]]
    result = {
        "sheetTypes": types.update_many(
            {"series": {"$exists": True}}, {"$unset": {"series": ""}}).modified_count,
        "sheets": 0,
        "downloads": downloads.update_many(
            {"sheet.seriesId": {"$exists": True}},
            {"$unset": {"sheet.seriesId": ""}}).modified_count,
        "indexDropped": None, "codes": 0, "conflicts": [],
    }

    # Las fichas que comparten tipo y número no caben en el índice nuevo: se informan
    pipeline = [{"$match": {"isDeleted": False}},
                {"$group": {"_id": SON([("t", "$sheetType"), ("n", "$number")]),
                            "codes": {"$push": "$code"}, "count": {"$sum": 1}}},
                {"$match": {"count": {"$gt": 1}}}]
    conflicted = set()
    for row in sheets.aggregate(pipeline):
        result["conflicts"].append(sorted(code or u"?" for code in row["codes"]))
        conflicted.add((row["_id"]["t"], row["_id"]["n"]))

    # El índice viejo se borra antes: sin seriesId, dos fichas con el mismo número chocarían
    for name, info in sheets.index_information().items():
        if info.get("key") == OLD_SHEET_INDEX_KEY:
            sheets.drop_index(name)
            result["indexDropped"] = name

    prefixes = {t["_id"]: t["codePrefix"] for t in types.find({}, {"codePrefix": 1})}
    for raw in sheets.find({}, {"sheetType": 1, "number": 1, "code": 1, "isDeleted": 1}):
        update = {"$unset": {"seriesId": ""}}
        prefix = prefixes.get(raw.get("sheetType"))
        clash = (not raw.get("isDeleted")
                 and (raw.get("sheetType"), raw.get("number")) in conflicted)
        if prefix and raw.get("number") and not clash:
            code = u"{}-{}".format(prefix, raw["number"])
            if code != raw.get("code"):
                update["$set"] = {"code": code}
                result["codes"] += 1
        result["sheets"] += sheets.update_one({"_id": raw["_id"]}, update).modified_count

    if not result["conflicts"]:
        VademecumSheet.ensure_indexes()
    return result


# --- Permiso del backoffice (BO-01) ---

PERMISSION_ENTITY = u"Vademécum"
PERMISSION_ENTITY_DEV_NAME = "vademecum"
PERMISSION_ACTION = "vademecum_admin"
PERMISSION_ACTION_LABEL = u"Administrar Vademécum"
# Roles que reciben el permiso al crearlo; AmbLeMa puede darlo a otros desde "Roles"
PERMISSION_DEFAULT_ROLES = ("superadmin", "admin")


def ensure_vademecum_permission():
    """Crea la entidad "Vademécum" con su acción y la activa en superadmin y admin.

    Idempotente: sirve para instalaciones nuevas y como script para los roles de producción.
    - Todo rol sin la entidad la recibe (así aparece en "Roles" para darla a otros); activa
      solo en los roles por defecto.
    - Un rol que ya la tiene no se toca: se respeta lo que AmbLeMa haya decidido.
    No se confía en Entity.post_save para propagarla: escribe los roles en la colección
    `entities` (bug previo) y no llega a `roles`.
    Devuelve {"entityCreated": bool, "rolesAdded": [devName...], "rolesGranted": [...]}.
    """
    from app.models.entity_model import Action, Entity
    from app.models.role_model import ActionHandler, Permission, Role

    entity = Entity.objects(devName=PERMISSION_ENTITY_DEV_NAME, isDeleted=False).first()
    created = entity is None
    if created:
        entity = Entity(name=PERMISSION_ENTITY, devName=PERMISSION_ENTITY_DEV_NAME,
                        actions=[Action(name=PERMISSION_ACTION, label=PERMISSION_ACTION_LABEL,
                                        sort=1)])
        entity.save()

    added, granted = [], []
    for role in Role.objects(isDeleted=False):
        if role.permissions.filter(entityId=str(entity.id)).first() is not None:
            continue
        allowed = role.devName in PERMISSION_DEFAULT_ROLES
        role.permissions.append(Permission(
            entityId=str(entity.id), entityName=entity.name,
            actions=[ActionHandler(name=PERMISSION_ACTION, label=PERMISSION_ACTION_LABEL,
                                   sort=1, allowed=allowed)]))
        role.save()
        added.append(role.devName or str(role.id))
        if allowed:
            granted.append(role.devName)
    return {"entityCreated": created, "rolesAdded": sorted(added),
            "rolesGranted": sorted(granted)}
