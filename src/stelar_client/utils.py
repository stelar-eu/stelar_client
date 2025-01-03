#
# Various heplper functions that do not belong in the API
#
from __future__ import annotations
from typing import TYPE_CHECKING

from .proxy import Proxy

if TYPE_CHECKING:
    from .client import Client


__all__ = [
    'client_for'
]

def client_for(proxy: Proxy) -> Client:
    return proxy.proxy_registry.catalog

