from __future__ import annotations
from typing import Optional, TYPE_CHECKING, TypeVar, Generic, Any
from uuid import UUID
from weakref import WeakValueDictionary
from .exceptions import InvalidationError
from .decl import ProxyState

if TYPE_CHECKING:
    from ..client import Client
    from .property import RefList
    from .registry import Registry

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
    proxy_registry: The Registry instance that this proxy belongs to
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

    def __init__(self, registry: Registry, eid: Optional[str|UUID] = None, entity=None):
        self.proxy_registry = registry
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
            self.proxy_sync(entity)

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

    def proxy_from_entity(self, entity: Any):
        """Update the proxy_attr dictionary from a given entity."""
        if self.proxy_attr is None:
            self.proxy_attr = dict()
        for prop in self.proxy_schema.properties.values():
            if not prop.isId:
                prop.convert_entity_to_proxy(self, entity)
    
    def proxy_to_entity(self, attrset: set[str]|dict[str,Any]|None = None):
        """Return an entity from the proxy values. 

        Note that the entity returned will not contain the id attribute.
        
        Args:
            attrset (set of property names, optional): If not None, 
                determines the set of names to add to the entity.

                Any type of object, where the expression
                `name in attrset` is valid, can be used.
                                
                Use this to only add names of changed properties to
                an entity:
                self.proxy_to_entity(self.proxy_changed)

        Returns:
            entity (dict): An entity dict containing all values 
                specified.
        """
        entity = dict()
        for prop in self.proxy_schema.properties.values():
            if prop.isId or (attrset is not None and prop.name not in attrset):
                continue
            prop.convert_proxy_to_entity(self, entity)
        return entity


    def proxy_sync(self, entity=None):
        """Sync the data between the proxy and the API entity.

        After a sync, the proxy is CLEAN and consistent with the
        underlying entity in the Data Catalog.  This method must be 
        overloaded in subclasses, to cater to the details of different 
        types of entities.
        
        In order to sync, the method works as follows:

        1. If the proxy is DIRTY: 
            - updates are sent to the API. 
            - The API optionally returns a new entity object. If so, set 
        `entity` to the new object. 
            - Make object CLEAN (by setting proxy_changed to None)

        2. If `entity` is None: load `entity` from API

        3. Update the proxy data from the new entity. This may involve
           updating additional proxies with data contained in the given
           entity.

        For typical operations, the implementation can use the following mathods:
        ```
        self.proxy_from_entity(entity)
        self.proxy_to_entity(attrset) -> entity
        ```
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


