from __future__ import annotations
from typing import Optional, TYPE_CHECKING, TypeVar, Generic, Any
from uuid import UUID
from io import StringIO
from .exceptions import EntityError
from .fieldvalidation import AnyField, UUIDField, NameField
from .proxy import Proxy
from .proxylist import ProxySublist
from .registry import Registry

if TYPE_CHECKING:
    from ..client import Client

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
    def __init__(self, *, validator=None, updatable=False, optional=False, 
                 entity_name=None, doc=None, create_default=None, short=None):
        """Constructs a proxy property descriptor
        
        Args:
            validator (FieldValidator)
            updatable (bool): If false, property cannot be set
            optional (bool): If false, property cannot be deleted
            entity_name (str|None): Corresponds to the entity field name. If not given,
                the same as the property name.
            doc (str|None): A piece of text that describes the property. This is
                used to form the full documentation for the property.
            create_default (Any): used to initialize new entities, when the user does not
                provide a value.
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
        self.__doc__ = self.autodoc(doc, self.validator.repr_type(), self.validator.repr_constraints())

    def autodoc(self, doc, repr_type, repr_constraints):
        INDENT = '    '
        out = StringIO()
        if doc is not None:
            print(doc, file=out)
        else:
            print(f"The '{self.name}' field", file=out)
        print(INDENT, f"Type: {repr_type}", file=out)
        for c in repr_constraints:
            print(INDENT, c, file=out)
        if self.updatable:
            print(INDENT, "updtatable", file=out)
        if self.optional:
            print(INDENT, "deletable", file=out)
        if self.entity_name != self.name:
            print(INDENT, "JSON field:", self.entity_name, file=out)

        return out.getvalue()

    def __set_name__(self, owner, name):
        if not issubclass(owner, Proxy):
            raise TypeError(f"Class {owner.__qualname__} must inherit from class Proxy")
        self.owner = owner
        self.name = name
        if self.entity_name is None:
            self.entity_name = name

    def check_value(self, value):
        if value is ... and not self.optional:
            raise ValueError(f"Property '{self.name}' is not optional")
        return value

    def get(self, obj):
        """Low-level getter """
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

    def convert_entity_to_proxy(self, proxy: Proxy, entity: Any):
        """Update proxy dict to represent this property from the entity"""
        if self.optional:
            entity_value = entity.get(self.entity_name, ...)
        else:
            try:
                entity_value = entity[self.entity_name]
            except KeyError as e:
                raise EntityError(f"Entity does not have attribute {self.entity_name}") from e
            
        proxy.proxy_attr[self.name] = (self.validator.convert_to_proxy(entity_value)
                                       if entity_value is not None else None)

    def convert_proxy_to_entity(self, proxy: Proxy, entity: dict):
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
            entity[self.entity_name] = self.validator.convert_to_entity(proxy_value)

    def convert_to_create(self, client: Client, proxy_type, create_props, entity_props):
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
        proxy_value = self.validator.validate(proxy_value, proxy=None)
        if proxy_value is None:
            entity_value = None
        else:
            entity_value = self.validator.convert_to_entity(proxy_value)
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
        super().__init__(validator=UUIDField(nullable=False), entity_name=entity_name, doc=doc)
        self.isId = True
    
    def __get__(self, obj, objtype=None):
        return obj.proxy_id

    def __set__(self, obj, value):
        raise AttributeError("Entity ID attribute cannot be set")
    
    def __delete__(self, obj):
        raise AttributeError("Entity ID attribute cannot be deleted")


class NameId(Property):
    def __init__(self, entity_name=None, doc=None):
        if doc is None:
            doc = "The name field, which is a unique string identifying the entity."
        super().__init__(validator=NameField, entity_name=entity_name, doc=doc)
        self.isName = True


class RefField(AnyField):
    """This field validator is specialized for reference properties"""

    def __init__(self, ref_property: Reference, ref_typename:str, **kwargs):
        super().__init__(**kwargs)
        self.ref_property = ref_property
        self.ref_typename = ref_typename
        self.add_check(self.to_uuid, 5)

    @property
    def proxy_type(self):
        return self.ref_property.proxy_type

    def to_uuid(self, value, **kwargs):
        if not isinstance(value, self.proxy_type):
            raise ValueError(f"Expected {self.proxy_type.__name__}")
        assert isinstance(value.proxy_id, UUID)
        return value.proxy_id, True

    def convert_to_proxy(self, value: str, **kwargs) -> UUID:
        return UUID(value)

    def convert_to_entity(self, value: UUID, **kwargs) -> str:
        return str(value)

    def repr_type(self):
        return self.ref_typename


class Reference(Property):
    """A proxy property which is a reference to an entity.
    """
    def __init__(self, proxy_type, nullable=False, trigger_sync=False, *args, **kwargs):
        ptn = self.property_type_name(proxy_type)
        val = RefField(self, ptn, nullable=nullable)
        super().__init__(*args, validator=val, **kwargs)
        self.__proxy_type = proxy_type
        self.nullable = nullable
        self.trigger_sync = trigger_sync

    @classmethod
    def property_type_name(cls, proxy_type) -> str:
        if isinstance(proxy_type, str):
            return proxy_type
        else:
            return proxy_type.__name__

    @property
    def proxy_type(self):
        """The class of the proxy object pointed to by this"""
        if isinstance(self.__proxy_type, str):
            from .schema import Schema
            self.__proxy_type = Schema.for_entity(self.__proxy_type).cls
        return self.__proxy_type

    def registry_for(self, obj) -> Registry:
        """Return the registry for the referrent, given owner"""
        return obj.proxy_registry.catalog.registry_for(self.proxy_type)

    def get(self, obj):
        """Low-level getter """
        if obj.proxy_attr is None:
            obj.proxy_sync()
        if obj.proxy_attr[self.name] is None:
            return None
        else:
            return self.registry_for(obj).fetch_proxy(obj.proxy_attr[self.name])

    def __get__(self, obj, objtype=None):
        val = self.get(obj)

        # The attribute is deleted
        if val is ...:
            raise AttributeError(f"Property '{self.name}' is not present")
        return val




class RefList(Reference):
    """A proxy property that manages a sub-schema (a sub-collection of other properties)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def property_type_name(cls, proxy_type) -> str:
        ptnb = super().property_type_name(proxy_type)
        return f"List[{ptnb}]"

    def get(self, obj):
        """Low-level getter """
        if obj.proxy_attr is None:
            obj.proxy_sync()
        return obj.proxy_attr[self.name]

    def __get__(self, obj, obj_type=None):
        if obj.proxy_attr is None:
            obj.proxy_sync()
        return ProxySublist(self, obj)
        
    def convert_entity_to_proxy(self, proxy, entity):
        entities = entity[self.entity_name]
        # entities is a list of entities, we need to fetch them from
        # our proxy's client.
        entity_id_name = self.proxy_type.proxy_schema.id.entity_name
        proxy_ids = [
            e.get(entity_id_name)
            for e in entities
        ]
        proxy.proxy_attr[self.name] = proxy_ids

    def convert_proxy_to_entity(self, proxy, entity):
        pass
