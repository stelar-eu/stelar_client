from __future__ import annotations
from typing import Optional, TYPE_CHECKING, TypeVar, Generic, Any
from uuid import UUID
from .exceptions import EntityError
from .fieldvalidation import AnyField, UUIDField
from .proxy import ProxyObj

class ProxyProperty:
    """A Python descriptor for implementing access and updating of
       fields of proxy objects.
    """
    def __init__(self, *, validator=None, updatable=False, optional=False, entity_name=None, doc=None):
        """Constructs a proxy proerty descriptor"""
        self.updatable = updatable
        self.isId = False
        self.optional = optional
        if validator is None:
            self.validator = AnyField()
        elif isinstance(validator, type):
            self.validator = validator()
        else:
            self.validator = validator
        self.entity_name = entity_name
        self.owner = self.name = None
        if doc is not None:
            self.__doc__ = doc

    def __set_name__(self, owner, name):
        if not issubclass(owner, ProxyObj):
            raise TypeError(f"Class {owner.__qualname__} must inherit from class ProxyObj")
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

    def set(self, obj, value):
        """Low-level setter"""
        value = self.validator.validate(value)
        if obj.proxy_changed is None:
            # Initialize proxy_changed on clean object
            if obj.proxy_attr is None:
                obj.proxy_sync()
            obj.proxy_changed = {self.name: obj.proxy_attr[self.name]}
        elif self.name not in obj.proxy_changed:
            # Record only first change
            obj.proxy_changed[self.name] = obj.proxy_attr[self.name]
        
        # update the value
        obj.proxy_attr[self.name] = value

    def convert_entity_to_proxy(self, proxy: ProxyObj, entity: Any):
        """Update proxy dict to represent this property from the entity"""
        if self.optional:
            entity_value = entity.get(self.entity_name, ...)
        else:
            try:
                entity_value = entity[self.entity_name]
            except KeyError as e:
                raise EntityError(f"Entity does not have attribute {self.entity_name}") from e
            
        proxy.proxy_attr[self.name] = self.validator.convert_to_proxy(entity_value)

    def convert_proxy_to_entity(self, proxy: ProxyObj, entity: dict):
        """Update entity dict to represent this property from the proxy.        
           The `changes` flag is true when the proxy_attr is actually the ProxyObj.proxy_changes
           dict.
        """
        proxy_value = proxy.proxy_attr[self.name]
        if proxy_value is ...:
            return
        entity[self.entity_name] = self.validator.convert_to_entity(proxy_value)

    def __get__(self, obj, objtype=None):
        val = self.get(obj)

        # The attribute is deleted
        if val is ...:
            raise AttributeError(f"Property '{self.name}' is not present")
        return val

    def __set__(self, obj, value):
        if value is ...:
            raise ValueError("Properties cannot be set to '...'")
        if not self.updatable:
            raise AttributeError(f"Property '{self.name}' is read-only")
        self.set(obj, value)

    def __delete__(self, obj):
        if obj.proxy_attr is None:
            obj.proxy_sync()
        if obj.proxy_attr[self.name] is ...:
            raise AttributeError(f"{self.name} is not present")
        if not self.optional:
            raise AttributeError(f"Property '{self.name}' is not optional")
        self.set(obj, ...)


class ProxyId(ProxyProperty):
    """A Python descriptor for implementing entity ID access."""

    def __init__(self, entity_name=None, doc=None):
        if doc is None:
            doc = "The ID"
        super().__init__(validator=UUIDField(nullable=False), entity_name=entity_name, doc=doc)
        self.isId = True
        self.types = UUID
    
    def __get__(self, obj, objtype=None):
        return obj.proxy_id

    def __set__(self, obj, value):
        raise AttributeError("Entity ID attribute cannot be set")
    
    def __delete__(self, obj):
        raise AttributeError("Entity ID attribute cannot be deleted")



class ProxyReference(ProxyProperty):
    """A proxy property which is a reference to an entity.
    """
    def __init__(self, proxy_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__proxy_type = proxy_type

    @property
    def proxy_type(self) -> ProxyClass:
        """The class of the proxy object pointed to by this"""
        if isinstance(self.__proxy_type, str):
            self.__proxy_type = ProxySchema.for_entity(self.__proxy_type).cls
        return self.__proxy_type

    def convert_entity_to_proxy(self, proxy, entity):
        return super().convert_entity_to_proxy(proxy, entity)

    def convert_proxy_to_entity(self, proxy, entity):
        return super().convert_proxy_to_entity(proxy, entity)
        

class ProxySubset(ProxyReference):
    """A proxy property that manages a sub-schema (a sub-collection of other properties)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __get__(self, obj, obj_type=None):
        from .proxy import SubCollection
        if obj.proxy_attr is None:
            obj.proxy_sync()
        return SubCollection(self, obj)
        
