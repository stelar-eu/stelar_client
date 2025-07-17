from __future__ import annotations

from .fieldvalidation import AnyField, JSONField
from .property import Property
from .proxy import Proxy


class ExtrasProperty(Property):
    def __init__(self, **kwargs):
        super().__init__(
            updatable=False, optional=False, validator=AnyField(default={}), **kwargs
        )
        self.isExtras = True
        self.item_validator = JSONField(nullable=True)

    def autodoc(self, doc, repr_type, repr_constraints):
        return """\
The field holding extras (additional fields) for this entity.
This field should not be accessed directly, instead its contents
are available as normal attributes.
"""

    def get(self, obj: Proxy):
        """Low-level getter"""
        if obj.proxy_attr is None:
            obj.proxy_sync()
        return obj.proxy_attr[self.name]

    def touch(self, obj: Proxy) -> bool:
        """Mark the extras as changed.

        This overloads the default touch, because after the touch, the
        extras dict needs to be copied (else, changing the 'proxy_attr' instance
        will change the 'proxy_changed' instance, which is not what we want).
        """
        if super().touch(obj):
            # Copy the extras dict to ensure that changes to the proxy_attr
            # do not affect the proxy_changed.
            obj.proxy_changed[self.name] = self.get(obj).copy()
            return True
        return False

    def __get__(self, obj, obj_type=None):
        return self.get(obj).copy()

    def convert_entity_to_proxy(self, proxy: Proxy, entity, **kwargs):
        entity_extras = entity.get(self.entity_name, {})
        proxy_extras = entity_extras.copy()  # Do we need a copy here?
        proxy.proxy_attr[self.name] = proxy_extras

    def convert_proxy_to_entity(self, proxy: Proxy, entity: dict, **kwargs):
        proxy_extras = proxy.proxy_attr[self.name]
        if proxy_extras is ...:
            return
        entity_extras = proxy_extras.copy()  # Do we need a copy here?
        entity[self.entity_name] = entity_extras

    def convert_to_create(self, proxy_type, create_props, entity_props, **kwargs):
        schema = proxy_type.proxy_schema

        # Collect all entries that do not appear in the schema
        entity_extras = {
            key: self.item_validator.validate(value, **kwargs)
            for key, value in create_props.items()
            if key not in schema.all_fields and value is not None
        }
        entity_props[self.entity_name] = entity_extras


class ExtrasProxy(Proxy, entity=False):
    """The class implements a Proxy with an 'extras' field.

    There are two API variants for extra arguments in the
    CKAN data catalog:
    * Resource entities allow additional fields in their objects.::

        "foo": "bar"

    * Packages, Groups and Organizations maintain a separate
      field called extras, whose format is a list of dicts.::

        "extras": [{"key": "foo", "value": "bar"}]

    Our own implementation follows the resource approach, by utilizing
    dynamic attributes.
    """

    def __getattr__(self, attr):
        try:
            return self.proxy_schema.extras.get(self)[attr]
        except KeyError as e:
            raise AttributeError(attr) from e

    def __setattr__(self, attr, value):
        if (
            attr.startswith("proxy_")
            or attr in self.proxy_schema.all_fields
            or hasattr(self.__class__, attr)
        ):
            return object.__setattr__(self, attr, value)

        extras_property = self.proxy_schema.extras
        value = extras_property.item_validator.validate(value)
        extras_property.touch(self)
        extras_property.get(self)[attr] = value
        self.proxy_autocommit()

    def __delattr__(self, attr):
        if (
            attr.startswith("proxy_")
            or attr in self.proxy_schema.all_fields
            or hasattr(self.__class__, attr)
        ):
            return object.__delattr__(self, attr)

        extras_property = self.proxy_schema.extras
        extras = extras_property.get(self)
        if attr in extras:
            extras_property.touch(self)
            # del extras[attr]
            del extras_property.get(self)[attr]
            self.proxy_autocommit()
        else:
            raise AttributeError(attr)
