from __future__ import annotations
from typing import Iterator, Optional, TYPE_CHECKING, TypeVar, Generic, Any
from uuid import UUID
from weakref import WeakValueDictionary
from datetime import datetime

if TYPE_CHECKING:
    from .client import Client

"""
    Introduction
    ------------

    Proxy objects represent STELAR entities in Python:
    - Datasets
    - Resources
    - Workflows
    - Groups
    - Organizations
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

    Proxy values
    -------------

    The proxied entity fields (attributes) have two representations: one
    that appears in the JSON object (stored in a dict) and one that is used
    by the proxy objects.

    client proxy value  <-->  json entity value

    For example, dates are represented as datetime objects in the proxy and as strings
    in the JSON entity.

    Conversion between the two is done via the two conversion methods of this class.
    Furthermore, when setting data a validation can be executed.

    This class implements base behaviour: no conversion is performed and validation
    always succeeds. In general, this is unwanted, but it is the default
"""

class FieldValidator:
    """Provide simple validation and conversion for entity fields. 
    
        A validation is a sequence of checks. Each check can:
        - Raise an exception of ValueError
        - Apply a value conversion and continue
        - Apply a value conversion and terminate
    
    Any function that takes as input a value, and returns a pair (newvalue, done)
    where `done` is a boolean, can be used as a check.

    At the end of all conversions, if no conversion signaled `done`, the `strict` attribute
    is checked. If True, an error is raised, else (the default) conversion succeeds.
    """

    def __init__(self, *, 
                 strict: bool=False, 
                 nullable: bool = True, 
                 minimum_value: Any = None, maximum_value: Any = None,
                 maximum_len: Optional[int]=None, minimum_len: Optional[int]=None):
        
        self.prioritized_checks = []
        self.checks = []
        self.strict = strict
        self.nullable = nullable
        self.minimum_value = minimum_value
        self.maximum_value = maximum_value
        self.maximum_len = maximum_len
        self.minimum_len = minimum_len

        if nullable is not None:
            self.add_check(self.check_null, -1)
        
        if minimum_value is not None:
            self.add_check(self.check_minimum, 10)
        if maximum_value is not None:
            self.add_check(self.check_maximum, 12)
        if maximum_len is not None or minimum_len is not None:
            self.add_check(self.check_length, 20)

    def add_check(self, check_func, pri: int):
        self.prioritized_checks.append((check_func, pri))
        self.prioritized_checks.sort(key= lambda p: p[1])
        self.checks = [p[0] for p in self.prioritized_checks]

    @staticmethod
    def check_null(value):
        if value is None:
            if self.nullable:
                return None, True
            else:
                raise ValueError("None is not allowed")
        else:
            return value, False
        
    def check_length(self, value):
        l = len(value)
        if self.minimum_len is not None and l < self.minimum_len:
            raise ValueError(f"The length ({l}) is less than the minimum ({self.minimum_len})")
        if self.maximum_len is not None and l > self.maximum_len:
            raise ValueError(f"The length ({l}) is greater that the maximum ({self.maximum_len})")
        return value, False

    def check_minimum(self, value):
        if v < self.minimum_value:
            raise ValueError(f"Value ({value}) too low (minimum={self.minimum})")
        return value, False

    def check_maximum(self, value):
        if v > self.maximum_value:
            raise ValueError(f"Value ({value}) too high (maximum={self.maximum})")
        return value, False

    def validate(self, value):
        done = False
        for check in self.checks:
            value, done = check(value)
            if done:
                return value
        if self.strict:
            raise ValueError("Validation failed to match input value")
        else:
            return value
        
    def convert_to_proxy(self, value):
        raise NotImplementedError()
    def convert_to_entity(self, value):
        raise NotImplementedError()


class AnyField(FieldValidator):
    """A very promiscuous basic validator."""
    def convert_to_proxy(self, value):
        return value
    def convert_to_entity(self, value):
        return value


class BasicField(FieldValidator):
    def __init__(self, ftype, **kwargs):
        super().__init__(**kwargs)
        self.ftype = ftype
        self.add_check(self.to_ftype, 5)

    def to_ftype(self, value):
        if not isinstance(value, self.ftype):
            value = self.ftype(value)
        return value, True


class StrField(BasicField):
    def __init__(self, **kwargs):
        super().__init__(ftype=str, **kwargs)


class IntField(BasicField):
    def __init__(self, **kwargs):
        super().__init__(ftype=int, **kwargs)


class BoolField(BasicField):
    def __init__(self, **kwargs):
        super().__init__(ftype=bool, **kwargs)


class DateField(FieldValidator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_check(self.to_date, 5)

    def to_date(self, value: Any) -> (datetime, bool):
        if isinstance(value, str):
            return datetime.fromisoformat(value), True
        elif isinstance(value, datetime):
            return value, True
        else:
            raise ValueError("Invalid type, expected datetime or string")

    def convert_to_entity(self, value: datetime) -> str:
        return value.to
    def convert_to_proxy(self, value: str) -> datetime:
        return datetime.fromisoformat(value)


class UUIDField(BasicField):
    def __init__(self, **kwargs):
        super().__init__(ftype=UUID, **kwargs)
    def convert_to_proxy(self, value: str) -> UUID:
        return UUID(value)
    def convert_to_entity(self, value: UUID) -> str:
        return str(value)





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

    def loaded_attributes(self, entity):
        """Return an object suitable for 'proxy_attr' from an entity object"""
        return {
            prop.name: prop.check_value(entity.get(prop.entity_name, ...))
            for prop in self.properties.values()
            if not prop.isId
        }

    @staticmethod
    def check_non_entity(cls):
        for prop in cls.__dict__.values():
            if isinstance(prop, ProxyProperty):
                raise TypeError(f"Class {cls.__qualname__} has properties defined but is not an entity")


class ProxyObj:
    """Base class for all proxy objects of the STELAR entities.

    Proxy objects are managed by ProxyCache. The primary implementation
    of ProxyCache is Client.

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

    def __init__(self, cache: ProxyCache, eid: Optional[str|UUID] = None, entity=None):
        self.proxy_cache = cache
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

    @classmethod
    def get_entity_id(cls, entity) -> str:
        return cls.proxy_schema.get_id(entity)

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
    def __init__(self, *, validator=None, updatable=False, optional=False, entity_name=None, doc=None):
        """Constructs a proxy proerty descriptor"""
        self.updatable = updatable
        self.isId = False
        self.optional = optional
        self.validator = validator if validator is not None else AnyField()
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


ProxyClass = TypeVar('ProxyClass', bound=ProxyObj)


class ProxyCache(Generic[ProxyClass]):
    def __init__(self, client: Client, proxy_type):
        self.client = client
        self.cache = WeakValueDictionary()
        self.proxy_type = proxy_type
    
    def fetch_proxy(self, eid: UUID) -> ProxyClass:
        proxy = self.cache.get(eid, None)
        if proxy is None:
            proxy = self.proxy_type(cache=self, eid=eid)
            self.cache[proxy.proxy_id] = proxy
        return proxy

    def fetch_proxy_for_entity(self, entity) -> ProxyClass:
        eid = UUID(self.proxy_type.get_entity_id(entity))
        proxy: ProxyObj = self.cache.get(eid, None)
        if proxy is None:
            proxy = self.proxy_type(cache=self, entity=entity)
            self.cache[proxy.proxy_id] = proxy
        else:
            if proxy.proxy_clean():
                proxy.proxy_attr = proxy.proxy_schema.loaded_attributes(entity)                
            else:
                raise RuntimeError("Proxy fetched with new entity on dirty state")
        return proxy


class ProxySubset(ProxyProperty):
    """A proxy property that manages a sub-schema (a sub-collection of other properties)
    """

    def __init__(self, proxy_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__proxy_type = proxy_type

    @property
    def proxy_type(self):
        if isinstance(self.__proxy_type, str):
            self.__proxy_type = ProxySchema.for_entity(self.__proxy_type).cls
        return self.__proxy_type

    def __get__(self, obj, obj_type=None):
        if obj.proxy_attr is None:
            obj.proxy_sync()
        return SubCollection(self, obj)
        

class SubCollection:
    """A proxy class that translates collection operations to operations
       on an entity sub-collection.
    """

    owner: ProxyObj

    def __init__(self, property: ProxySubset, owner: ProxyObj):
        self.property = property
        self.owner = owner

    @property
    def __coll(self):
        return self.property.get(self.owner)

    def __iter__(self):
        return iter(self.__coll)
    
    def __len__(self):
        return len(self.__coll)

    def __getitem__(self, key):
        return self.__coll[key]
    
    def __delitem__(self, key):
        raise NotImplementedError(f"delitem  {self.property.owner.__name__}.{self.property.name}")

    def __iadd__(self, **kwargs):
        raise NotImplementedError(f"iadd {self.property.owner.__name__}.{self.property.name}")
