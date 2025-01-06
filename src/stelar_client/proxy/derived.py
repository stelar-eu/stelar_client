from __future__ import annotations
from typing import Optional, TYPE_CHECKING, TypeVar, Generic, Any
from uuid import UUID
from io import StringIO
from .exceptions import EntityError
from .fieldvalidation import AnyField, UUIDField, NameField
from .proxy import Proxy
from .proxylist import ProxySublist
from .registry import Registry
from .property import Property


class derived_property(Property):
    """Derived properties are used to cache some 'expensive' value into the proxy.

    The value is recomputed at each proxy_sync(), during a call to 'proxy_from_entity()'.
    This value is then returned by the getter. Additional 'vanilla python properties' or
    methods can be declared in the usual way, to implement richer functionality.
    """

    def __init__(self, method=None, **kwargs):
        super().__init__(updatable=False, optional=False, create_default=None, **kwargs)
        self.method = method

    # Disable mutating ops
    def set(self, obj, value):
        pass

    def __call__(self, method):
        self.method = method
        return self

    def convert_entity_to_proxy(self, proxy: Proxy, entity: Any):
        proxy.proxy_attr[self.name] = self.method(proxy, entity)

    def convert_proxy_to_entity(self, proxy: Proxy, entity: dict):
        pass

    def convert_to_create(self, create_props: Entity, entity_props: Entity):
        if self.name in create_props:
            raise EntityError("Cannot provide derived property for creation")
            
    