import geojson

from .proxy.fieldvalidation import AnyField


class GeoJSON(AnyField):
    """
    A field for GeoJSON data.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(repr_type="GeoJSON", *args, **kwargs)
        self.add_check(self.to_geojson, 5)

    def to_geojson(self, value):
        try:
            value = geojson.GeoJSON.to_instance(value, strict=True)
        except ValueError:
            raise
        except Exception as e:
            raise ValueError("Invalid format for GeoJSON object") from e
        if not isinstance(value, geojson.GeoJSON):
            raise ValueError(f"Invalid object for GeoJSON: {value}")
        if not value.is_valid:
            raise ValueError(f"Invalid GeoJSON object: {value.errors()}")
        return value, False

    def convert_to_proxy(self, value, **kwargs):
        if value is None:
            return None
        return geojson.GeoJSON.to_instance(value)

    def convert_to_entity(self, value, **kwargs):
        return value

    def default_value(self):
        if hasattr(self, "default"):
            return self.default
        elif self.nullable:
            return None
        else:
            raise NotImplementedError()

    def repr_type(self):
        return self._repr_type
