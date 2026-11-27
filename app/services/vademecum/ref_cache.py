# -*- coding: utf-8 -*-
"""Resolución por lotes de `ReferenceField` en serializadores de listados.

Evita el N+1: una sola consulta `id__in` por colección referenciada y un dict por id.
Las referencias rotas se dejan fuera del dict para que el serializador siga devolviendo
`None`, como hacía la dereferencia directa.
"""


def ref_id(value):
    """ObjectId de la referencia sin dereferenciarla (DBRef, ObjectId o documento)."""
    return getattr(value, "id", value) if value is not None else None


def refs(model, values, fields=()):
    """{str(id): documento} para los ids distintos de `values` que existan en `model`."""
    ids = []
    for value in values:
        ref = ref_id(value)
        if ref is not None and ref not in ids:
            ids.append(ref)
    if not ids:
        return {}
    query = model.objects(id__in=ids)
    if fields:
        query = query.only(*fields)
    return {str(item.id): item for item in query}
