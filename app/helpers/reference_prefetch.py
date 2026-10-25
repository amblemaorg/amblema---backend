# /app/helpers/reference_prefetch.py


from bson import DBRef, ObjectId
from mongoengine import fields as me_fields


def _refId(ref):
    if isinstance(ref, DBRef):
        return ref.id
    if isinstance(ref, ObjectId):
        return ref
    return None


def prefetchReferences(records, schema):
    """
    Bulk-loads the documents behind the schema's MAReferenceField fields
    (one query per field, only the attributes MAReferenceField serializes),
    instead of letting each record dereference them one by one during dump.
    Records must be loaded without touching those fields beforehand.
    References that can't be resolved are left untouched, so dump behaves
    exactly as before for them.
    """
    from app.helpers.ma_schema_fields import MAReferenceField

    if not records:
        return records

    modelFields = getattr(records[0], '_fields', {})
    for name, field in schema.fields.items():
        if not isinstance(field, MAReferenceField):
            continue
        attr = field.attribute or name
        modelField = modelFields.get(attr)
        if not isinstance(modelField, me_fields.ReferenceField):
            continue

        ids = set()
        for record in records:
            refId = _refId(record._data.get(attr))
            if refId is not None:
                ids.add(refId)
        if not ids:
            continue

        RefModel = modelField.document_type
        if 'field' in field.metadata:
            needed = [field.metadata['field']]
        elif 'fields' in field.metadata:
            needed = list(field.metadata['fields'])
        else:
            needed = ['name']
        needed = [f for f in needed if f != 'id']

        query = RefModel.objects
        if all(f in RefModel._fields for f in needed):
            query = query.only(*needed)
        related = query.in_bulk(list(ids))

        for record in records:
            refId = _refId(record._data.get(attr))
            if refId is not None and refId in related:
                record._data[attr] = related[refId]
    return records
