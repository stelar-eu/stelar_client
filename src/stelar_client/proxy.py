from __future__ import annotations
from typing import Iterator
from uuid import UUID

"""
    Proxy objects represent STELAR entities in Python:
    - Datasets
    - Resources
    - Workflows

    - Processes (workflow executions)
    - Tasks
    - Tools
    
    - Policies
    - Users 
      
    They can be used to
    - inspect 
    - update
    - delete
    - link and relate
    - plus, custom operations

    The proxy object base class implements generic handling of properties:
    - initializing properties
    - loading propertties on demand
    - updating single properties
    - updating multiple properties
"""


class ProxySchema:
    """ A class that holds all information related to an entity proxy class.
        This includes the list of proxied properties, and other information
    """
    def __init__(self, cls):
        self.cls = cls
        self.properties = {}
        self.id = None

        # Initialize the properties list
        # N.B. This does not check the superclasses
        for name,prop in cls.__dict__.items():
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

    def loaded_attributes(self, entity):
        """Return an object suitable for 'proxy_attr' from an entity object"""
        return {
            prop.name: prop.check_value(entity.get(prop.entity_name, ...))
            for prop in self.properties.values()
            if not prop.isId
        }


    @staticmethod
    def check_non_entity(cls):
        for name,prop in cls.__dict__.items():
            if isinstance(prop, ProxyProperty):
                raise TypeError(f"Class {cls.__qualname__} has properties defined but is not an entity")

class ProxyObj:
    """Base class for all proxy objects of the STELAR entities.

    Attributes are used to hold property values:
    proxy_id: The UUID of the proxies entity
    proxy_attr: 
        A dict of all loaded attributes. When None, the entity has
        not yet been loaded
    proxy_changed:
        A dict of all changed attributes (loaded values of updated attributes) 
        since last upload. When None, the entity is clean.

    To initialize a proxy object, one must supply either an entity id or
    an entity JSON body.
    """

    def __init__(self, eid=None, entity=None):
        if eid is None and entity is None:
            raise ValueError("A proxy must be initialized either with an entity ID" 
                             " or with an entity JSON object containing the ID")

        if entity is not None:
            if eid is None:
                try:
                    eid = entity[self.proxy_schema.id.entity_name]
                except KeyError as e:
                    raise ValueError("A proxy must be initialized either with an entity ID" 
                                " or with an entity JSON object containing the ID") from e
            # this is a check which is not really necessary...
            elif self.proxy_schema.id.entity_name in entity:
                if str(eid) != str(entity[self.proxy_schema.id.entity_name]):
                    raise ValueError("Mismatch between entity ID provided directly and indirectly")

        if not isinstance(eid, UUID):
            self.proxy_id = UUID(eid)
        else:
            self.proxy_id = eid

        if entity is not None:
            self.proxy_attr = self.proxy_schema.loaded_attributes(entity)
        else:
            self.proxy_attr = None
        self.proxy_changed = None


    def __init_subclass__(cls, entity=True):
        if entity:
            cls.proxy_schema = ProxySchema(cls)
        else:
            # cls is not an entity class, check that 
            # there are no properties defined on it
            ProxySchema.check_non_entity(cls)

    def proxy_fetch(self) -> dict:
        """Subclasses use this to read the current entity from the API"""
        raise NotImplementedError
    
    def proxy_update(self, updates: dict, orig: dict):
        """Subclasses use this to update the current entity using the dict
        
        updates: The current values of properties
        orig: The original values of changed properties
        """
        raise NotImplementedError

    def proxy_clean(self):
        """Return true if the current proxy object is clean."""
        return self.proxy_changed is None

    def proxy_sync(self):
        """Sync the data between the proxy and the API entity."""

        if self.proxy_attr is not None and self.proxy_changed is not None:
            new_entity = {
                prop.entity_name: self.proxy_attr[prop.name]
                for prop in self.proxy_schema.properties.values()
                if self.proxy_attr[prop.name] is not ...
            }
            changes = {
                prop.entity_name: self.proxy_changed[prop.name]
                for prop in self.proxy_schema.properties.values()
                if prop.name in self.proxy_changed
            }
            entity = self.proxy_update(new_entity, changes)
        else:
            entity = self.proxy_fetch()

        self.proxy_attr = self.proxy_schema.loaded_attributes(entity)
        self.proxy_changed = None


class ProxyProperty:
    """A Python descriptor for implementing access and updating of
       fields of proxy objects.
    """
    def __init__(self, *, updatable=False, optional=False, entity_name=None, doc=None):
        """Constructs a proxy proerty descriptor"""
        self.updatable = updatable
        self.isId = False
        self.optional = optional
        self.types = object
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

    def __get__(self, obj, objtype=None):
        if obj.proxy_attr is None:
            obj.proxy_sync()
        val = obj.proxy_attr[self.name]

        # The attribute is deleted
        if val is ...:
            raise AttributeError(f"Property '{self.name}' is not present")
        return val

    def set(self, obj, value):

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
            raise AttributeError(f"{self.name}")
        if not self.optional:
            raise AttributeError(f"Property '{self.name}' is not optional")
        self.set(obj, ...)


class ProxyId(ProxyProperty):
    """A Python descriptor for implementing entity ID access."""

    def __init__(self, entity_name=None, doc=None):
        if doc is None:
            doc = "The ID"
        super().__init__(entity_name=entity_name, doc=doc)
        self.isId = True
        self.types = UUID
    
    def __get__(self, obj, objtype=None):
        return obj.proxy_id

    def __set__(self, obj, value):
        raise AttributeError("Entity ID attribute cannot be set")
    
    def __delete__(self, obj):
        raise AttributeError("Entity ID attribute cannot be deleted")

