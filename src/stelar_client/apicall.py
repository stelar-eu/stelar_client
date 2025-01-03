"""
    Facility for calling the STELAR API.

    The functions in this file will be changed (together with this documentation)
    as the API implementation progresses.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Type, TypeVar, Generic, Iterator
from .backdoor import CKAN
from functools import wraps
from uuid import UUID
from .utils import *
from .proxy import (Proxy, ProxyOperationError, ProxyCursor, 
                    ProxyList, Reference, RefList, ProxySynclist, EntityNotFound, 
                    ErrorState,
                    ProxyState)

if TYPE_CHECKING:
    from .client import Client
ProxyClass = TypeVar('ProxyClass', bound=Proxy)


class api_call:
    """Class that exposes the CKAN API.

        `api_call(proxy).foo(...)`
        returns the 'result' of the CKAN API response on success, 
        and raises a ProxyOperationError on failure.

        `api_call(client).foo(...)`
        does the same.
    """
    def __init__(self, arg: Proxy|Client):
        from .client import Client
        if isinstance(arg, Proxy):
            self.proxy = arg
            self.client = client_for(self.proxy)
            self.proxy_id = self.proxy.proxy_id
            self.proxy_type = type(self.proxy)
        elif isinstance(arg, Client):
            self.proxy = None
            self.client = arg
            self.proxy_id = None
            self.proxy_type = None
        self.ckan = self.client.DC

    def __getattr__(self, name):
        func = getattr(self.ckan, name)
        @wraps(func)
        def wrapped_call(*args, **kwargs):
            response = func(*args, **kwargs)
            if not response['success']:
                err = response['error']
                if err['__type'] == 'Not Found Error':
                    raise EntityNotFound(self.proxy_type, self.proxy_id, name)
                else:
                    # Generic 
                    raise ProxyOperationError(self.proxy_type, self.proxy_id, name, response['error'])
            return response['result']
        return wrapped_call

    def get_call(self, proxy_type, op):
        _map_to_ckan = {
            'Dataset': 'package',
            'Resource': 'resource',
            'Organization': 'organization',
            'Group': 'group',
        }
        ckan_type = _map_to_ckan[proxy_type.__name__]
        if ckan_type == 'package' and op=='purge':
            call_name = 'dataset_purge'
        else:
            call_name = f"{ckan_type}_{op}"
        return getattr(self, call_name)


def generic_proxy_sync(proxy: Proxy, entity):
    proxy_type = type(proxy)
    ac = api_call(proxy)

    if proxy.proxy_state is ProxyState.ERROR:
        raise ErrorState(proxy)

    if proxy.proxy_changed is not None:
        updates = proxy.proxy_to_entity(proxy.proxy_changed)
        patch = ac.get_call(proxy_type, 'patch')

        try:
            entity = patch(id=str(proxy.proxy_id), **updates)
        except EntityNotFound as e:
            proxy.proxy_is_purged()
            raise  # We have updates that are lost

        proxy.proxy_changed = None
    if entity is None:
        show = ac.get_call(proxy_type, 'show')
        try:
            entity = show(id=str(proxy.proxy_id))
        except EntityNotFound as e:
            proxy.proxy_is_purged()
            return  # Not an error!
    proxy.proxy_from_entity(entity)
    
    


def generic_create(client: Client, proxy_type: Type[ProxyClass], **properties) -> ProxyClass:
    schema = proxy_type.proxy_schema
    entity_properties = {}
    for property in schema.properties.values():        
        property.convert_to_create(client, proxy_type, properties, entity_properties)

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
    

def generic_get(client: Client, proxy_type: Type[ProxyClass], name_or_id, default=None) -> ProxyClass:
    ac = api_call(client)
    show = ac.get_call(proxy_type, "show")
    try:
        entity = show(id=str(name_or_id))
    except EntityNotFound as e:
        return default
    return client.registry_for(proxy_type).fetch_proxy_for_entity(entity)


def generic_fetch_list(client: Client, proxy_type: Type[ProxyClass], *, limit: int, offset: int) -> list[str]:
    ac = api_call(client)
    _list = ac.get_call(proxy_type, "list")
    result = _list(limit=limit, offset=offset)

    return result

def generic_fetch(client: Client, proxy_type: Type[ProxyClass], *, limit: int, offset: int) -> Iterator[ProxyClass]:
    ac = api_call(client)
    _list = ac.get_call(proxy_type, "list")
    result = _list(limit=limit, offset=offset)
    show = getattr(ac, f"{ckan_type}_show")
    registry = client.registry_for(proxy_type)

    for name in result:
        entity = show(id=name)
        yield registry.fetch_proxy_for_entity(entity)


def generic_delete(proxy: Proxy, purge=False):
    psl = ProxySynclist()
    psl.on_delete(proxy)

    ac = api_call(proxy)
    
    delete = ac.get_call(type(proxy), 'purge' if purge else 'delete')
    delete(id=str(proxy.proxy_id))
    psl.sync()

# 
# The generic base classes for proxy and cursor
#  

class GenericProxy(Proxy, entity=False):

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


class GenericCursor(ProxyCursor[ProxyClass]):
    def create(self, **prop) -> ProxyClass:
        return generic_create(self.client, self.proxy_type, **prop)
    
    def get(self, name_or_id: str|UUID, default: ProxyClass=None) -> ProxyClass:
        return generic_get(self.client, self.proxy_type, name_or_id, default=default)

    def fetch_list(self, *, limit: int, offset: int) -> list[str]:
        return generic_fetch_list(self.client, self.proxy_type, limit=limit, offset=offset)

    def fetch(self, *, limit: int, offset: int) -> Iterator[ProxyClass]:
        yield from generic_fetch(self.client, self.proxy_type, limit=limit, offset=offset)

    def __getitem__(self, item):
        v = super().__getitem__(item)
        if isinstance(v, list):
            return GenericProxyList(v, self.client, self.proxy_type)
        else:
            return v
