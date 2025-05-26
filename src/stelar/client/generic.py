"""
    Facility for calling the STELAR API.

    The functions in this file will be changed (together with this documentation)
    as the API implementation progresses.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, Type, TypeVar
from uuid import UUID

# from .api_call import api_call_DC as api_call
from .api_call import api_call
from .proxy import (
    EntityNotFound,
    ErrorState,
    Id,
    Proxy,
    ProxyCursor,
    ProxyList,
    ProxyState,
    ProxySynclist,
    Registry,
)

if TYPE_CHECKING:
    from .client import Client
ProxyClass = TypeVar("ProxyClass", bound=Proxy)


def generic_proxy_sync(proxy: Proxy, entity, update_method="patch"):
    """Perform proxy_sync(entity) using the api_call class.

    Args:
        proxy (Proxy): the proxy to sync
        entity (Entity|None): the entity to sync from
        update_method: one of 'update' or 'patch'
    """
    if update_method not in ("update", "patch"):
        raise ValueError("Update method must be either 'patch' or 'update'")
    proxy_type = type(proxy)
    ac = api_call(proxy)

    if proxy.proxy_state is ProxyState.ERROR:
        raise ErrorState(proxy)

    if proxy.proxy_id == UUID(int=0):
        # Create the entity !
        entity_properties = proxy.proxy_to_entity()
        # Populate sync list
        psl = ProxySynclist()
        psl.on_create_proxy(proxy)

        # Create the entity
        create = ac.get_call(type(proxy), "create")
        entity = create(**entity_properties)

        # We add this proxy to its registry
        proxy.proxy_registry.register_proxy_for_entity(proxy, entity)
        proxy.proxy_from_entity(entity)
        proxy.proxy_changed = None

        # Sync around
        psl.sync()

    else:
        # The entity exists, make a normal sync

        if proxy.proxy_changed is not None:
            # A proper update is needed
            if update_method == "patch":
                updates = proxy.proxy_to_entity(proxy.proxy_changed)
                update_call = ac.get_call(proxy_type, "patch")
            elif update_method == "update":
                updates = proxy.proxy_to_entity()
                update_call = ac.get_call(proxy_type, "update")

            try:
                entity = update_call(id=str(proxy.proxy_id), **updates)
            except EntityNotFound:
                proxy.proxy_is_purged()
                raise  # We have updates that are lost
            proxy.proxy_changed = None

        if entity is None:
            show = ac.get_call(proxy_type, "show")
            try:
                entity = show(id=str(proxy.proxy_id))
            except EntityNotFound:
                proxy.proxy_is_purged()
                return  # Not an error!

        proxy.proxy_from_entity(entity)


def generic_create(
    client: Client, proxy_type: Type[ProxyClass], **properties
) -> ProxyClass:
    entity_properties = proxy_type.new_entity(client, **properties)

    # Populate the sync list
    psl = ProxySynclist()
    psl.on_create(proxy_type, properties)

    # Create the entity
    ac = api_call(client)
    create = ac.get_call(proxy_type, "create")
    new_entity = create(**entity_properties)
    registry = client.registry_for(proxy_type)
    new_proxy = registry.fetch_proxy_for_entity(new_entity)

    # Sync around
    psl.sync()
    return new_proxy


def generic_get(
    client: Client, proxy_type: Type[ProxyClass], name_or_id, default=None
) -> ProxyClass:
    ac = api_call(client)
    show = ac.get_call(proxy_type, "show")
    try:
        entity = show(id=str(name_or_id))
    except EntityNotFound:
        return default
    return client.registry_for(proxy_type).fetch_proxy_for_entity(entity)


def generic_fetch_list(
    client: Client, proxy_type: Type[ProxyClass], *, limit: int, offset: int, **kwargs
) -> list[str]:
    ac = api_call(client)
    _list = ac.get_call(proxy_type, "list")
    result = _list(limit=limit, offset=offset, **kwargs)

    return result


def generic_fetch_old(
    client: Client, proxy_type: Type[ProxyClass], *, limit: int, offset: int, **kwargs
) -> Iterator[ProxyClass]:
    ac = api_call(client)
    _list = ac.get_call(proxy_type, "list", **kwargs)
    result = _list(limit=limit, offset=offset)

    registry = client.registry_for(proxy_type)

    # Check it the list already contains entities
    if result and isinstance(result[0], dict):
        for entity in result:
            yield registry.fetch_proxy_for_entity(entity)
    else:
        show = ac.get_call(proxy_type, "show")
        for name in result:
            entity = show(id=name)
            yield registry.fetch_proxy_for_entity(entity)


def generic_fetch(
    client: Client, proxy_type: Type[ProxyClass], *, limit: int, offset: int, **kwargs
) -> Iterator[ProxyClass]:
    ac = api_call(client)
    _fetch = ac.get_call(proxy_type, "fetch", **kwargs)
    result = _fetch(limit=limit, offset=offset)

    registry = client.registry_for(proxy_type)

    # Check it the list already contains entities
    for entity in result:
        yield registry.fetch_proxy_for_entity(entity)


def generic_delete(proxy: Proxy, purge=False):
    psl = ProxySynclist()
    psl.on_delete(proxy)

    ac = api_call(proxy)

    delete = ac.get_call(type(proxy), "purge" if purge else "delete")
    delete(id=str(proxy.proxy_id))
    psl.sync()


#
# The generic base classes for proxy and cursor
#


class GenericProxy(Proxy, entity=False):
    id = Id()

    def delete(self, purge=False):
        """
        Delete the entity proxied by this proxy.

        If the entity is purged then the deletion is permanent.
        After the purge deletion, the proxy is left in the ERROR state.

        Otherwise, the deletion removes the entity from the active
        ones, but the entity can still be accessed. Searches will
        not return the entity.

        TODO: Implement entity reclamation for non-purged entities!
        """
        generic_delete(self, purge=purge)
        super().delete(purge=purge)

    def proxy_sync(self, entity=None):
        """Sync the proxy with the entity in the API."""
        return generic_proxy_sync(self, entity)


class GenericProxyList(ProxyList):
    def __init__(self, eid_list, client, proxy_type):
        """A proxy list using a list of ids or names.

        The resolving is done using 'generic_get()'
        """

        super().__init__(client, proxy_type)
        self._data = eid_list

    @property
    def coll(self):
        return self._data

    def resolve_proxy(self, item):
        return generic_get(self.client, self.proxy_type, item)


class GenericCursor(ProxyCursor[ProxyClass], Registry[ProxyClass]):
    def create(self, **prop) -> ProxyClass:
        return self.proxy_type.new(self.client, **prop)

    def get(
        self, name_or_id: str | UUID, default: ProxyClass | None = None
    ) -> ProxyClass:
        return generic_get(self.client, self.proxy_type, name_or_id, default=default)

    def fetch_list(self, *, limit: int, offset: int) -> list[str]:
        return generic_fetch_list(
            self.client, self.proxy_type, limit=limit, offset=offset
        )

    def fetch(self, *, limit: int, offset: int) -> Iterator[ProxyClass]:
        yield from generic_fetch(
            self.client, self.proxy_type, limit=limit, offset=offset
        )

    def __getitem__(self, item):
        v = super().__getitem__(item)
        if isinstance(v, list):
            return GenericProxyList(v, self.client, self.proxy_type)
        else:
            return v

    def _ipython_key_completions_(self):
        try:
            kc = self.fetch_list(limit=100, offset=0)
        except Exception:
            kc = []
        return kc
