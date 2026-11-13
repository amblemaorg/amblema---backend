# -*- coding: utf-8 -*-
# app/helpers/vademecum_seeds.py
"""Índices y semillas iniciales del módulo Vademécum (API-01).

Las semillas solo crean lo que falta y nunca actualizan lo existente: lo que el administrador
edite desde el backoffice no se pisa. Colores de HT/IM/MX y las áreas son provisionales
(DIS-01 y la lista de AmbLeMa en S2).
"""

from app.models.vademecum import (
    VADEMECUM_MODELS, SheetSeries, VademecumSheetType, VademecumArea, VademecumSiteContent)

SHEET_TYPES = (
    dict(codePrefix="HT", name=u"Hora TAL", headerName=u"Hora TAL", color="#F2A93B", sort=1,
         series=()),
    dict(codePrefix="IM", name=u"Ingenio Matemático", headerName=u"Ingenio Matemático",
         color="#2F80ED", sort=2,
         series=(dict(code="34", name=u"3.º y 4.º grado", grades=["3", "4"], sort=1),
                 dict(code="56", name=u"5.º y 6.º grado", grades=["5", "6"], sort=2))),
    dict(codePrefix="MX", name=u"Momento X", headerName=u"Momento X", color="#1F3A68", sort=3,
         series=()),
    dict(codePrefix="AM", name=u"Ambiente", headerName=u"Ambiente", color="#94C021", sort=4,
         series=()),
)

AREAS = (
    (u"Comprensión lectora", 1),
    (u"Geometría", 2),
    (u"Operaciones matemáticas", 3),
    (u"Geografía", 4),
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
        values = dict(data)
        values["series"] = [SheetSeries(**s) for s in data["series"]]
        VademecumSheetType(**values).save()
        created["sheetTypes"] += 1

    # Áreas provisionales solo en una base sin áreas: renombrarlas o borrarlas no las recrea
    if VademecumArea.objects.count() == 0:
        for name, sort in AREAS:
            VademecumArea(name=name, sort=sort).save()
            created["areas"] += 1

    for key in SITE_CONTENT_KEYS:
        if VademecumSiteContent.objects(key=key).first():
            continue
        VademecumSiteContent(key=key).save()
        created["siteContent"] += 1

    return created


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
