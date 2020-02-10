# /app/helpers/ma_schema_fields.py


from marshmallow import fields

from app.helpers.handler_images import upload_image
from app.services.generic_service import getRecordOr404


class MAPolygonField(fields.Field):
    """Marshmallow field that validate a polygon field
    """

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return ""
        coordinates = []
        for coordinate in value["coordinates"][0]:
            coordinates.append({"lat": coordinate[0], "lng": coordinate[1]})
        return coordinates

    def _deserialize(self, value, attr, data, **kwargs):
        polygon = {"type": "Polygon", "coordinates": [value]}
        return polygon


class MAReferenceField(fields.Field):
    """Marshmallow field that validate a reference field
    """

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return ""
        if "field" in self.metadata:
            record = {
                "id": str(value["id"]),
                self.metadata["field"]: value[self.metadata["field"]]}
        else:
            record = {"id": str(value["id"]), "name": value["name"]}
        return record

    def _deserialize(self, value, attr, data, **kwargs):
        if 'document' in self.metadata:
            record = getRecordOr404(self.metadata['document'], value)
            return record
        else:
            return value


class MAImageField(fields.Field):
    """Marshmallow field that validate a image field
    """

    def _deserialize(self, value, attr, data, **kwargs):
        if str(value).startswith('data'):
            return upload_image(value)
        return value
