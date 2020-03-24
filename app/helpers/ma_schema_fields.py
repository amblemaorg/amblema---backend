# /app/helpers/ma_schema_fields.py


from flask import current_app
from marshmallow import fields, validate, ValidationError

from app.helpers.handler_images import upload_image
from app.services.generic_service import getRecordById


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

    default_error_messages = {
        "invalid": [{"status": "5", "msg": "Record not found"}]
    }

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

            record = getRecordById(self.metadata['document'], value)
            if not record:
                raise self.make_error("invalid")
            return record
        else:
            return value


class MAImageField(fields.Field):
    """Marshmallow field that validate a image field
    """

    def _deserialize(self, value, attr, data, **kwargs):
        """
        custom metadata:
          folder: folder name into image resource path
          size: optional size limit of image, in MB
        """
        if str(value).startswith('data'):

            size = None if not 'size' in self.metadata else self.metadata['size']
            return upload_image(value, self.metadata['folder'], size)
        return value
