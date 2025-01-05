from __future__ import annotations
from typing import Optional, TYPE_CHECKING, TypeVar, Generic, Any
from .proxy import Proxy
from .property import Property, Id, NameId


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

    # Declare attributes
    properties: dict[str, Property]

    # Class attribute, registers schemas for entity names.
    entity_schema: dict[str, Schema] = dict()


    @classmethod
    def for_entity(cls, name: str) -> Schema:
        """Return the schema for the given named entity
        
        Args:
            name (str): the name of an entity (e.g. 'Dataset', 'Group', etc)
        Returns:
            the schema for the give entity, or None.
        """
        return cls.entity_schema.get(name)

    @property
    def class_name(self):
        """Return the class name for the"""
        return self.cls.__name__

    def __init__(self, cls):
        """The proxy class for this schema.
        """
        self.cls = cls
        self.properties = {}
        self.id = None
        self.name_id = None
        self.extras = None
        self.all_fields = dict()
        self.all_entity_fields = set()

        # Initialize the properties list
        # N.B. This does not check the superclasses
        for name, prop in cls.__dict__.items():
            if isinstance(prop, Property):
                if prop.isId:
                    assert isinstance(prop, Id)
                    if self.id is not None:
                        raise TypeError(f"Multiple ID attributes defined for {cls.__qualname__}")
                    self.id = prop
                elif prop.isName:
                    assert isinstance(prop, NameId)
                    if self.name_id is not None:
                        raise TypeError(f"Multiple nameID attributes defined for {cls.__qualname__}")
                    self.name_id = prop
                    # Name is added to the properties !
                    self.properties[name] = prop
                elif prop.isExtras:
                    if self.extras is not None:
                        raise TypeError(f"Multiple nameID attributes defined for {cls.__qualname__}")
                    self.extras = prop
                    # Extras is added to the properties !
                    self.properties[name] = prop
                else:
                    self.properties[name] = prop

                # Add the name to all_fields
                self.all_fields[name] = prop
                self.all_entity_fields.add(prop.entity_name)

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
        """Return a 'short list' of important field names.

        The main purpose for this is to provide a reduced set of names to
        use in visual representations of proxy instances.
        """
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
