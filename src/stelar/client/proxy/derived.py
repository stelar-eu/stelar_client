from __future__ import annotations

from typing import Any

from .exceptions import EntityError
from .property import Property
from .proxy import Proxy


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

    def convert_entity_to_proxy(self, proxy: Proxy, entity: Any, **kwargs):
        proxy.proxy_attr[self.name] = self.method(proxy, entity)

    def convert_proxy_to_entity(self, proxy: Proxy, entity: dict, **kwargs):
        pass

    def convert_to_create(
        self, proxy_type, create_props: dict, entity_props: dict, **kwargs
    ):
        if self.name in create_props:
            raise EntityError("Cannot provide derived property for creation")
