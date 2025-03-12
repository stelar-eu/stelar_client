#
# Various heplper functions that do not belong in the API
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .proxy import Proxy, ProxyCursor, ProxyList, Registry

if TYPE_CHECKING:
    from .client import Client

from .proxy.decl import (
    TAGSPEC_PATTERN,
    tag_join,
    tag_split,
    validate_tagname,
    validate_tagspec,
)

__all__ = [
    "client_for",
    "tag_split",
    "tag_join",
    "validate_tagspec",
    "validate_tagname",
    "TAGSPEC_PATTERN",
]


def client_for(obj: Any) -> Client:
    """Return the client for a proxy object."""
    from .client import Client

    match obj:
        case Proxy():
            return obj.proxy_registry.catalog
        case ProxyList():
            return obj.client
        case ProxyCursor():
            return obj.client
        case Registry():
            return obj.catalog
        case Client():
            return obj
        case _:
            raise RuntimeError(
                f"Cannot resolve client for type {obj.__class__.__qualname__}", obj
            )
