from __future__ import annotations

from typing import TYPE_CHECKING, Any, Type, TypeVar

from .property import Property
from .proxy import Proxy
from .proxylist import ProxyList
from .refs import Reference

if TYPE_CHECKING:
    from ..client import Client
    from .property import RefList
    from .registry import Registry
    from .schema import Schema

ProxyClass = TypeVar("ProxyClass", bound=Proxy)


class ProxySynclist:
    """A container for the proxies that need to be sync'd after
    an operation.
    """

    def __init__(self, l: list[Proxy] = []):
        self.tosync = list()
        for a in l:
            self.add(a)

    def add(self, ref: Proxy | ProxyList):
        """Add a proxy or the elements of a proxy list to the synclist.

        Any other types are ignored.
        """
        if isinstance(ref, ProxyList):
            for p in ref:
                self.add(p)
        elif isinstance(ref, Proxy):
            self.tosync.append(ref)

    def trigger_properties(self, schema: Schema):
        for p in schema.properties.values():
            if isinstance(p, Reference) and p.trigger_sync:
                yield p

    def on_create(self, proxy_type: Type[ProxyClass], properties: dict[str, Any]):
        for p in self.trigger_properties(proxy_type.proxy_schema):
            self.add(properties.get(p.name))

    def on_create_proxy(self, proxy: ProxyClass):
        for p in self.trigger_properties(proxy.proxy_schema):
            self.add(p.get(proxy))

    def on_delete(self, proxy: Proxy):
        for p in proxy.proxy_schema.properties.values():
            # Add all present properties referenced from this property
            self.add(getattr(proxy, p.name, None))

    def on_update(self, proxy: Proxy, prop: Property, newref: Proxy):
        if isinstance(prop, Reference) and prop.trigger_sync:
            oldref = getattr(proxy, prop.name)
            self.add(oldref)
            self.add(newref)

    def on_update_all(self, proxy: ProxyClass):
        for p in self.trigger_properties(proxy.proxy_schema):
            self.add(p.get(proxy))

    def sync(self):
        for prx in self.tosync:
            prx.proxy_sync()
        self.tosync.clear()
