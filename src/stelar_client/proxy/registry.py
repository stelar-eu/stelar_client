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
    def __init__(self, catalog: RegistryCatalog, proxy_type):
        self.catalog = catalog
        self.registry = WeakValueDictionary()
        self.proxy_type = proxy_type
        if self.catalog is not None:
            self.catalog.add_registry_for(proxy_type, self)
    
    def fetch_proxy(self, eid: UUID) -> ProxyClass:
        if not isinstance(eid, UUID):
            eid = UUID(eid)
        proxy = self.registry.get(eid, None)
        if proxy is None:
            proxy = self.proxy_type(registry=self, eid=eid)
            assert proxy.proxy_id == eid
            self.registry[proxy.proxy_id] = proxy
        return proxy

    def fetch_proxy_for_entity(self, entity) -> ProxyClass:
        eid = UUID(self.proxy_type.get_entity_id(entity))
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

    def delete_proxy(self, proxy):
        if proxy.proxy_id is None:
            # Not an error to delete something in proxy state
            return 
        self.registry.pop(proxy.proxy_id, None)
        


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