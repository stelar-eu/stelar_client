from __future__ import annotations
from typing import Optional, TYPE_CHECKING, TypeVar, Generic, Type
from uuid import UUID
from weakref import WeakValueDictionary
from .exceptions import ConflictError
from .decl import ProxyState
from .proxy import Proxy

if TYPE_CHECKING:
    from ..client import Client
    from .property import RefList
ProxyClass = TypeVar('ProxyClass', bound=Proxy)


class Registry(Generic[ProxyClass]):
    """A registry is a factory and collection of proxies.

        The registry maintains a weak reference to its elements, so that
        a proxy which is not referenced any more, is deleted from the registry.

        Registries are crucial as they are used to maintain the following important
        invariant:
            'For each entity, there exists no more than one proxy (under the same client)
            at any time'.

        This invariant guarantees that, any updates to an entity (via a client)
        can only happen on a uniquely defined object. This solution saves on memory
        and avoids complex state synchronization problems.

        Registries are typed: only proxies of the same type belong to a registry.

        A collection of registries of different types form a 'catalog' (of type RegistryCatalog).

    """

    def __init__(self, catalog: RegistryCatalog, proxy_type):
        self.catalog = catalog
        self.registry = WeakValueDictionary()
        self.proxy_type = proxy_type
        if self.catalog is not None:
            self.catalog.add_registry_for(proxy_type, self)
    
    def fetch_proxy(self, eid: UUID) -> ProxyClass:
        """Return a proxy for the provided entity id.

           If a proxy needs to be created, it will be initialized in the
           EMPTY state by the provided entity object.

           Args:
            eid: The provided entity ID.
           Returns:
            a proxy initialized with the provided entity.
        """
        if not isinstance(eid, UUID):
            eid = UUID(eid)
        proxy = self.registry.get(eid, None)
        if proxy is None:
            proxy = self.proxy_type(registry=self, eid=eid)
            assert proxy.proxy_id == eid
            self.registry[proxy.proxy_id] = proxy
        return proxy

    def fetch_proxy_for_entity(self, entity) -> ProxyClass:
        """Return a proxy for the entity object provided.

           The returned proxy will be created if needed, and
           it will be initialized in the CLEAN state by the
           provided entity object.

           Args:
            entity: The provided entity object.
           Returns:
            a proxy initialized with the provided entity.
        """
        eid = UUID(self.proxy_type.proxy_schema.get_id(entity))
        proxy: Proxy = self.registry.get(eid, None)
        if proxy is None:
            proxy = self.proxy_type(registry=self, entity=entity)
            assert eid==proxy.proxy_id
            assert proxy.proxy_id not in self.registry
            self.registry[proxy.proxy_id] = proxy
            proxy.proxy_sync(entity)
        else:
            if proxy.proxy_state in (ProxyState.EMPTY, ProxyState.CLEAN):
                proxy.proxy_sync(entity)
            else:
                raise ConflictError(f"Proxy fetched with new entity on state {proxy.proxy_state}")
        return proxy


    def register_proxy_for_entity(self, proxy: Proxy, entity: Entity):
        """Register an existing proxy ebject for the given entity.

           For success, 
           1. the proxy id must be UUID(int=0)
           2. the entity must contain an id 
           3. the id must not exist in the registry already.

           On success, the entity id is copied into the proxy and the
           proxy is registered.

           On failure, a conflict error is raised.
        """
        if proxy.proxy_id is None:
            raise ConflictError(f"Cannot register deleted proxy")
        if proxy.proxy_id != UUID(int=0):
            raise ConflictError(f"Cannot register proxy with ID = {proxy.proxy_id}")
        eid = UUID(self.proxy_type.proxy_schema.get_id(entity))
        if eid in self.registry:
            raise ConflictError(f"Proxy for entity {eid} is already registered")

        # Success:
        proxy.proxy_id = eid
        self.registry[eid] = proxy


    def purge_proxy(self, proxy):
        if proxy.proxy_id is None:
            # Not an error to delete something in proxy state
            return 
        self.registry.pop(proxy.proxy_id, None)
        proxy.proxy_id = None
        


class RegistryCatalog:
    """Class that implements a catalog of registries, for different entity types.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.registry_catalog = dict[type, Registry]()

    def add_registry_for(self, cls: Type[ProxyClass], registry: Registry[ProxyClass]):
        """This method adds a registry to the catalog. It is often called from inside
           the constructor of a registry.
        """
        if cls in self.registry_catalog:
            if self.registry_catalog[cls] is not registry:
                raise ValueError(f"Cannot add multiple registries for entity {cls.__name__}")
        else:
            self.registry_catalog[cls] = registry

    def registry_for(self, cls: Type[ProxyClass]) -> Registry[ProxyClass]:
        """Return the registry for the given type.
        """
        return self.registry_catalog[cls]

    def registry_stats(self):
        """Return a Series with the number of proxies held for each entity type."""
        import pandas as pd
        return pd.Series({
            r.proxy_type.__name__: len(r.registry) for r in self.registry_catalog.values()
        })