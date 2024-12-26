from __future__ import annotations
from typing import Optional, TYPE_CHECKING, TypeVar, Generic, Any
from .property import ProxyProperty, ProxyId


#----------------------------------------------------------
#  Proxy Schema 
#
#  A collection of attributes defined for an entity.
#  Each attribute is an instance of ProxyProperty and 
#  contains metadata related to this attribute.
#----------------------------------------------------------

class ProxySchema:
    """ A class that holds all information related to an entity proxy class.
        This includes the list of proxied properties, and other information
    """

    entity_schema = dict()

    @classmethod
    def for_entity(cls, name: str) -> ProxySchema:
        """Return the schema for the given named entity"""
        return cls.entity_schema.get(name)

    @property
    def class_name(self):
        return self.cls.__name__

    properties: dict[str, ProxyProperty]

    def __init__(self, cls):
        self.cls = cls
        self.properties = {}
        self.id = None

        # Initialize the properties list
        # N.B. This does not check the superclasses
        for name, prop in cls.__dict__.items():
            if isinstance(prop, ProxyProperty):
                if prop.isId:
                    assert isinstance(prop, ProxyId)
                    if self.id is not None:
                        raise TypeError(f"Multiple ID attributes defined for {cls.__qualname__}")
                    self.id = prop
                else:
                    self.properties[name] = prop

        # check that we have specified an ID attribute, and add a default
        # ID attribute otherwise
        if self.id is None:
            # check that attribute 'id' is available!
            if hasattr(cls, 'id') or 'id' in self.properties:
                raise TypeError(f"A member named 'id' is present but it is not marked as entity ID")

            self.id = ProxyId()
            cls.id = self.id
            self.id.__set_name__(cls, 'id')

        # Register yourself
        self.entity_schema[self.class_name] = self

    def get_id(self, entity) -> str:
        """Return the entity ID from the entity object"""
        return entity[self.id.entity_name]
    
    def proxy_from_entity(self, proxy: ProxyObj, entity: Any):
        """Update the proxy_attr dictionary from a given entity."""
        if proxy.proxy_attr is None:
            proxy.proxy_attr = dict()
        for prop in self.properties.values():
            if not prop.isId:
                prop.convert_entity_to_proxy(proxy, entity)
    
    def proxy_to_entity(self, proxy: ProxyObj, attrset: set[str]|dict[str,Any]|None = None):
        """Return an entity from the proxy values. 
        
        Returns:
            entity (dict): An entity containing all values 
        """
        entity = dict()
        for prop in self.properties.values():
            if prop.isId or (attrset is not None and prop.name not in attrset):
                continue
            prop.convert_proxy_to_entity(proxy, entity)
        return entity

    @staticmethod
    def check_non_entity(cls):
        for prop in cls.__dict__.values():
            if isinstance(prop, ProxyProperty):
                raise TypeError(f"Class {cls.__qualname__} has properties defined but is not an entity")

