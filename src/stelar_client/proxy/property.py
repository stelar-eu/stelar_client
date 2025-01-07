from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar
from uuid import UUID

from .exceptions import EntityError
from .fieldvalidation import AnyField, NameField, UUIDField
from .proxy import Proxy
from .proxylist import ProxySublist
from .registry import Registry

if TYPE_CHECKING:
    from ..client import Client

Entity = dict[str, Any]


class Property:
    """A Python descriptor for implementing access and updating of
    fields of proxy objects.

    A property object performs the following roles:
     -   Is a python 'descriptor' (implements getter, setter and deleter) for
         proxy classes
     -   Holds a number of metadata that determine the behaviour of the proxy
         (validation, conversion to entity, nullabilty, updatability, optionality,
         view, etc)
     -   Performs internalization/externalization for the data.



    """

    def __init__(
        self,
        *,
        validator=None,
        updatable=False,
        optional=False,
        entity_name=None,
        doc=None,
        create_default=None,
        short=None,
    ):
        """Constructs a proxy property descriptor

        Args:
            validator (FieldValidator)
            updatable (bool): If false, property cannot be set
            optional (bool): If false, property cannot be deleted
            entity_name (str|None): Corresponds to the entity field name. If not given,
                the same as the property name.
            doc (str|None): A piece of text that describes the property. This is
                used to form the full documentation for the property.
            create_default (Any): If provided, it is used to initialize new entities,
                when the user does not provide a value. Note: this is an entity value!
            short (bool|None): Denotes whether this property is included in "short presentations"
                of the entity. If None, a heuristic based on the name and type is used.
        """
        self.updatable = updatable
        self.isId = False
        self.isName = False
        self.isExtras = False
        self.optional = optional
        if validator is None:
            self.validator = AnyField()
        elif isinstance(validator, type):
            self.validator = validator()
        else:
            self.validator = validator
        self.entity_name = entity_name
        self.owner = self.name = None
        self.create_default = create_default
        self.short = short
        self.doc = doc

    def autodoc(self, doc, repr_type, repr_constraints):
        INDENT = "    "
        out = StringIO()

        typespec = str(repr_type)
        constraints = list(repr_constraints)

        if "nullable" in repr_constraints:
            typespec += "|None"
            constraints.remove("nullable")

        if doc is None:
            doc = f"The '{self.name}' field"

        f = [typespec]

        fp = []
        if not self.updatable:
            fp.append("read-only")
        if self.optional:
            fp.append("deletable")
        if fp:
            f.append(f"({', '.join(fp)}):")
        else:
            f.append(":")

        f += [doc, *constraints]

        if self.entity_name != self.name:
            f += ["JSON field:", self.entity_name]

        print(INDENT, *f, file=out)
        return out.getvalue()

    @property
    def qualname(self):
        return f"{self.owner.__name__}.{self.name}"

    def __repr__(self):
        return f"<Property {self.qualname}>"

    def __str__(self):
        return self.qualname

    def __set_name__(self, owner, name):
        if not issubclass(owner, Proxy):
            raise TypeError(f"Class {owner.__qualname__} must inherit from class Proxy")
        self.owner = owner
        self.name = name
        if self.entity_name is None:
            self.entity_name = name
        self.__doc__ = self.autodoc(
            self.doc, self.validator.repr_type(), self.validator.repr_constraints()
        )

    def check_value(self, value):
        if value is ... and not self.optional:
            raise ValueError(f"Property '{self.name}' is not optional")
        return value

    def get(self, obj):
        """Low-level getter"""
        if obj.proxy_attr is None:
            obj.proxy_sync()
        return obj.proxy_attr[self.name]

    def touch(self, obj):
        """Transition the initial value of a clean proxy to the
        'proxy_changed' dictionary.

        This is done only on the first update to an attribute,
        in order to allow for the proxy_reset() functionality.
        """
        if obj.proxy_changed is None:
            # Initialize proxy_changed on clean object
            if obj.proxy_attr is None:
                obj.proxy_sync()
            obj.proxy_changed = {self.name: obj.proxy_attr[self.name]}
        elif self.name not in obj.proxy_changed:
            # Record only first change
            obj.proxy_changed[self.name] = obj.proxy_attr[self.name]

    def set(self, obj, value):
        """Low-level setter"""
        value = self.validator.validate(value)
        self.touch(obj)
        # update the value
        obj.proxy_attr[self.name] = value

    def convert_entity_to_proxy(self, proxy: Proxy, entity: Any, **kwargs):
        """Update proxy dict to represent this property from the entity"""
        if self.optional:
            entity_value = entity.get(self.entity_name, ...)
        else:
            try:
                entity_value = entity[self.entity_name]
            except KeyError as e:
                raise EntityError(
                    f"Entity does not have attribute {self.entity_name}"
                ) from e

        proxy.proxy_attr[self.name] = (
            self.validator.convert_to_proxy(entity_value, **kwargs)
            if entity_value is not None
            else None
        )

    def convert_proxy_to_entity(self, proxy: Proxy, entity: dict, **kwargs):
        """Update entity dict to represent this property from the proxy.
        The `changes` flag is true when the proxy_attr is actually the Proxy.proxy_changes
        dict.
        """
        proxy_value = proxy.proxy_attr[self.name]
        if proxy_value is ...:
            return
        if proxy_value is None:
            entity[self.entity_name] = None
        else:
            entity[self.entity_name] = self.validator.convert_to_entity(
                proxy_value, **kwargs
            )

    def convert_to_create(
        self, proxy_type: type, create_props: Entity, entity_props: Entity, **kwargs
    ):
        """Convert a value to be used for entity creation.

        Args:
            client (Client): The client used for creation.
            proxy_type (ProxyClass): The entity type being created.
            create_props: The object passed to the create client call
            entity_props: The entity object given to the create API call.
        """
        if self.name not in create_props:
            if self.create_default is not None:
                entity_props[self.entity_name] = self.create_default
            return
        proxy_value = create_props[self.name]
        proxy_value = self.validator.validate(proxy_value, **kwargs)
        if proxy_value is None:
            entity_value = None
        else:
            entity_value = self.validator.convert_to_entity(proxy_value, **kwargs)
        entity_props[self.entity_name] = entity_value

    def __get__(self, obj, objtype=None):
        val = self.get(obj)

        # The attribute is deleted
        if val is ...:
            raise AttributeError(f"Property '{self.name}' is not present")
        return val

    def __set__(self, obj, value):
        if not self.updatable:
            raise AttributeError(f"Property '{self.name}' is read-only")
        if value is ...:
            raise ValueError("Properties cannot be set to '...'")
        self.set(obj, value)
        if obj.proxy_autosync:
            obj.proxy_sync()

    def __delete__(self, obj):
        if not self.optional:
            raise AttributeError(f"Property '{self.name}' is not optional")
        if obj.proxy_attr is None:
            obj.proxy_sync()
        if obj.proxy_attr[self.name] is ...:
            raise AttributeError(f"{self.name} is not present")
        self.set(obj, ...)


class Id(Property):
    """A Python descriptor for implementing entity ID access."""

    def __init__(self, entity_name=None, doc=None):
        if doc is None:
            doc = "The ID"
        super().__init__(
            validator=UUIDField(nullable=False), entity_name=entity_name, doc=doc
        )
        self.isId = True

    def __get__(self, obj, objtype=None):
        return obj.proxy_id

    def __set__(self, obj, value):
        raise AttributeError("Entity ID attribute cannot be set")

    def __delete__(self, obj):
        raise AttributeError("Entity ID attribute cannot be deleted")


class NameId(Property):
    """Many entities have a name field with a unique constaint."""

    def __init__(self, entity_name=None, doc=None, validator=NameField):
        if doc is None:
            doc = "The name field, which is a unique string identifying the entity."
        super().__init__(validator=validator, entity_name=entity_name, doc=doc)
        self.isName = True
