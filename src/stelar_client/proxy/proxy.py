from __future__ import annotations
from typing import Optional, TYPE_CHECKING, TypeVar, Generic, Any
from uuid import UUID
from weakref import WeakValueDictionary
from .exceptions import InvalidationError
from .decl import ProxyState

if TYPE_CHECKING:
    from ..client import Client
    from .property import RefList

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

"""



#----------------------------------------------------------
#
# Proxy is the base class for all proxy classes
#
#----------------------------------------------------------



class Proxy:
    """Base class for all proxy objects of the STELAR entities.

    Proxy objects are managed by Registry. The primary implementation
    of Registry is Client.

    Attributes are used to hold property values:
    proxy_cache: The Registry instance that this proxy belongs to
    proxy_id: The UUID of the proxies entity
    proxy_attr:
        A dict of all loaded attributes. When None, the entity has
        not yet been loaded
    proxy_changed:
        A dict of all changed attributes (loaded values of updated attributes) 
        since last upload. When None, the entity is clean.

    To initialize a proxy object, one must supply either an entity id or
    an entity JSON body.

    A proxy can be in one of four states:
    EMPTY, CLEAN, DIRTY, ERROR


    """

    def __init__(self, cache: Registry, eid: Optional[str|UUID] = None, entity=None):
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

        self.proxy_attr = None
        self.proxy_changed = None
        if entity is not None:
            self.proxy_schema.proxy_from_entity(self, entity)

    def __init_subclass__(cls, entity=True):
        from .schema import Schema
        if entity:
            cls.proxy_schema = Schema(cls)
        else:
            # cls is not an entity class, check that 
            # there are no properties defined on it
            Schema.check_non_entity(cls)

    @classmethod
    def get_entity_id(cls, entity) -> str:
        return cls.proxy_schema.get_id(entity)

    @property
    def proxy_state(self) -> ProxyState:
        """Return the proxy state"""
        if self.proxy_id is None:
            return ProxyState.ERROR
        elif self.proxy_attr is None:
            return ProxyState.EMPTY
        elif self.proxy_changed is None:
            return ProxyState.CLEAN
        else:
            return ProxyState.DIRTY

    def proxy_invalidate(self, *, force=False):
        """Make this proxy object EMPTY, discarding any entity data.

        If the proxy object is DIRTY, a `InvalidationError` exception
        is raised, unless `force` is true.

        Args:
            force (bool): Invalidate even if DIRTY, without raising exception.
                Deafults to False.

        Raises:
            InvalidationError: If called on a DIRTY proxy with `force` being False
        """
        if self.proxy_changed is not None and not force:
            raise InvalidationError()
        self.proxy_attr = self.proxy_changed = None

    def proxy_reset(self):
        """If proxy is EMPTY, do nothing. 
           If the proxy is DIRTY, make it CLEAN by restoring the
           values changed since the last sync.
        """
        if self.proxy_changed is not None:
            for name,value in self.proxy_changed.items():
                self.proxy_attr[name] = value
            self.proxy_changed = None                        

    def proxy_sync(self):
        """Sync the data between the proxy and the API entity.

            After a sync, the proxy is CLEAN and consistent with the
            underlying entity in the Data Catalog.

            This method needs to be overloaded in subclasses.
            For typical operations, the method can use
            the following functions:

            ```
            self.proxy_schema.proxy_from_entity(self, entity)
            ```
            in order to update the proxy from a new entity dict.

            ```
            self.proxy_schema.proxy_to_entity(self, entity, change)
            ```
            in order to obtain a new entity object suitable for passing
            to the STELAR API.
        """
        raise NotImplementedError



class ProxyList:
    """A proxy class that translates collection operations to operations
       on an entity sub-collection.
    """

    owner: Proxy

    def __init__(self, property: RefList, owner: Proxy):
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


ProxyClass = TypeVar('ProxyClass', bound=Proxy)

class Registry(Generic[ProxyClass]):
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
        proxy: Proxy = self.cache.get(eid, None)
        if proxy is None:
            proxy = self.proxy_type(cache=self, entity=entity)
            self.cache[proxy.proxy_id] = proxy
        else:
            if proxy.proxy_clean():
                proxy.proxy_attr = proxy.proxy_schema.proxy_attributes(entity)                
            else:
                raise RuntimeError("Proxy fetched with new entity on dirty state")
        return proxy

