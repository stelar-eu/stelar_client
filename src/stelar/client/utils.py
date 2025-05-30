#
# Various heplper functions that do not belong in the API
#
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Type
from uuid import UUID

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


def convert_proxy_id_to_str(
    value: Proxy | UUID | str, proxy_type: Type = Proxy, *, nullable: bool = True
) -> str | None:
    """Convert a UUID or Proxy to a string representation."""
    if nullable:
        if value is None:
            return None
    if isinstance(value, proxy_type):
        if value.proxy_id is None:
            raise ValueError("Proxy has no ID")
        return str(value.proxy_id)
    elif isinstance(value, UUID):
        return str(value)
    elif isinstance(value, str):
        return value
    else:
        raise TypeError(f"Cannot convert proxy {value} of type {type(value)} to string")
