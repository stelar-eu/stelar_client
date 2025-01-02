from __future__ import annotations
from typing import Optional, TYPE_CHECKING, TypeVar, Generic, Any
from .proxy import Proxy
from .property import Property, Id


#----------------------------------------------------------
#  Proxy Schema 
#
#  A collection of attributes defined for an entity.
#  Each attribute is an instance of Property and 
#  contains metadata related to this attribute.
#----------------------------------------------------------

class Schema:
    """ A class that holds all information related to an entity proxy class.
        This includes the list of proxied properties, and other information
    """

    entity_schema = dict()

    @classmethod
    def for_entity(cls, name: str) -> Schema:
        """Return the schema for the given named entity"""
        return cls.entity_schema.get(name)

    @property
    def class_name(self):
        return self.cls.__name__

    properties: dict[str, Property]

    def __init__(self, cls):
        self.cls = cls
        self.properties = {}
        self.id = None

        # Initialize the properties list
        # N.B. This does not check the superclasses
        for name, prop in cls.__dict__.items():
            if isinstance(prop, Property):
                if prop.isId:
                    assert isinstance(prop, Id)
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

            self.id = Id()
            cls.id = self.id
            self.id.__set_name__(cls, 'id')

        # Register yourself
        self.entity_schema[self.class_name] = self

    def get_id(self, entity) -> str:
        """Return the entity ID from the entity object"""
        return entity[self.id.entity_name]    

    SHORT_NAMES = {
        'id', 'name', 'state', 'title', 'author', 'maintainer',
        'type', 'resource_type', 'url',
    }

    def short_list(self, additional={}):
        return [self.id.name]+[name
            for name, prop in self.properties.items()
            if (prop.short is True 
                or name in additional 
                or (prop.short is None and name in self.SHORT_NAMES))]

    @staticmethod
    def check_non_entity(cls):
        for prop in cls.__dict__.values():
            if isinstance(prop, Property):
                raise TypeError(f"Class {cls.__qualname__} has properties defined but is not an entity")
