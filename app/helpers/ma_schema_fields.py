# /app/helpers/ma_schema_fields.py


from marshmallow import fields

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