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
        proxy = self.registry.get(eid, None)
        if proxy is None:
            proxy = self.proxy_type(registry=self, eid=eid)
            self.registry[proxy.proxy_id] = proxy
        return proxy

    def fetch_proxy_for_entity(self, entity) -> ProxyClass:
        eid = UUID(self.proxy_type.get_entity_id(entity))
        proxy: Proxy = self.registry.get(eid, None)
        if proxy is None:
            proxy = self.proxy_type(registry=self, entity=entity)
            self.registry[proxy.proxy_id] = proxy
        else:
            if proxy.proxy_state is ProxyState.CLEAN:
                proxy.proxy_sync(entity)
            else:
                raise ConflictError("Proxy fetched with new entity on dirty state")
        return proxy


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
