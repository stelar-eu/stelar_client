from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from .proxy import Proxy

TagSpecList = tuple[str, ...]
TagDictList = list[dict[str, Any]]
ProxyClass = TypeVar("ProxyClass", bound="Proxy")
Entity = dict[str, Any]
