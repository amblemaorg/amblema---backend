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
        elif "fields" in self.metadata:
            record = {}
            for field in self.metadata['fields']:
                record[field] = str(value[field])
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
        elif str(value).startswith(current_app.config.get('SERVER_URL')):
            value = value.replace(current_app.config.get('SERVER_URL'), '')
        return value

    def _serialize(self, value, attr, data, **kwargs):
        if value and isinstance(value, str) and value.startswith("/resources/"):
            value = current_app.config.get('SERVER_URL') + value
        return value


def serialize_links(element):
    '''Recursive function for add server url to images and files'''

    if isinstance(element, list):
        for i in range(len(element)):
            a = serialize_links(element[i])
            element[i] = a
    elif isinstance(element, dict):
        for k, v in element.items():
            element[k] = serialize_links(v)
    elif isinstance(element, str) and element.startswith('/resources/'):
        element = current_app.config.get('SERVER_URL') + element
    return element
