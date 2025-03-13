from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Type, TypeVar
from uuid import UUID
from weakref import WeakValueDictionary

from .decl import ProxyState
from .exceptions import ConflictError
from .proxy import Proxy

if TYPE_CHECKING:
    pass
    # from ..client import Client
    # from .property import RefList
    # This seemed to create some kind of problem...
    # from .typing import ProxyClass


ProxyClass = TypeVar("ProxyClass", bound=Proxy)


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
            raise ValueError(f"Expected UUID, got {eid} of type {type(eid)}")
        if eid == UUID(int=0):
            raise ValueError("The null UUID(int=0) is not legal")
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

        Arguments:
            entity: The provided entity object.
        Returns:
            a proxy initialized with the provided entity.
        """
        eid = UUID(self.proxy_type.proxy_schema.get_id(entity))
        proxy: Proxy = self.registry.get(eid, None)
        if proxy is None:
            proxy = self.proxy_type(registry=self, entity=entity)
            assert eid == proxy.proxy_id
            assert proxy.proxy_id not in self.registry
            self.registry[proxy.proxy_id] = proxy
            proxy.proxy_sync(entity)
        else:
            if proxy.proxy_state in (ProxyState.EMPTY, ProxyState.CLEAN):
                proxy.proxy_sync(entity)
            else:
                raise ConflictError(
                    proxy,
                    entity,
                    f"Proxy fetched with new entity on state {proxy.proxy_state}",
                )
        return proxy

    def register_proxy_for_entity(self, proxy: Proxy, entity: dict):
        """Register an existing proxy ebject for the given entity.

        For success,
        1. the proxy id must be UUID(int=0)
        2. the entity must contain an id
        3. the id must not exist in the registry already.

        On success, the entity id is copied into the proxy and the
        proxy is registered.

        On failure, a conflict error is raised.

        Arguments:
            proxy: The proxy object to be registered.
            entity: The entity object to be registered.
        Returns:
            None
        Raises:
            ConflictError: If the proxy cannot be registered (is deleted or has an ID)

        """
        if proxy.proxy_id is None:
            raise ConflictError(proxy, entity, "Cannot register deleted proxy")
        if proxy.proxy_id != UUID(int=0):
            raise ConflictError(
                proxy, entity, f"Cannot register proxy with ID = {proxy.proxy_id}"
            )
        eid = UUID(self.proxy_type.proxy_schema.get_id(entity))
        if eid in self.registry:
            raise ConflictError(
                proxy, entity, f"Proxy for entity {eid} is already registered"
            )

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

    The purpose of the catalog is to provide all context information needed for
    data manipulation and transformation between proxy space and the STELAR API.

    Indeed, the RegistryCatalog class is intended to become one of the base classes
    of Client. However, it is a separate class, for better design and testability.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.registry_catalog = dict[type, Registry]()
        self.name_catalog = dict[str, Registry]()

        from .tag import VocabularyIndex

        self.vocabulary_index = VocabularyIndex(self)

    def add_registry_for(self, cls: Type[ProxyClass], registry: Registry[ProxyClass]):
        """This method adds a registry to the catalog. It is often called from inside
        the constructor of a registry.
        """
        if cls in self.registry_catalog:
            if self.registry_catalog[cls] is not registry:
                raise ValueError(
                    f"Cannot add multiple registries for entity {cls.__name__}"
                )
        else:
            self.registry_catalog[cls] = registry
            self.name_catalog[cls.__name__] = registry

    def registry_for(self, cls: Type[ProxyClass] | str) -> Registry[ProxyClass]:
        """Return the registry for the given type."""
        if isinstance(cls, str):
            return self.name_catalog[cls]
        else:
            return self.registry_catalog[cls]

    def registry_stats(self):
        """Return a Series with the number of proxies held for each entity type."""
        import pandas as pd

        return pd.Series(
            {
                r.proxy_type.__name__: len(r.registry)
                for r in self.registry_catalog.values()
            }
        )

    def fetch_active_vocabularies(self):
        """This method should return a list of dicts,
        {"name": "...",  "id": "..."}.

        More items are also allowed. It so happens that this is
        exactly the format returned by CKAN's  "vocabulary_list"
        API call. :-)
        """
        raise NotImplementedError
