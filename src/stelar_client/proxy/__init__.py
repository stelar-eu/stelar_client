"""
The STELAR client's proxying package.

The definitions here implement entity proxying by the client.
Entities include Data Catalog entities, authorization entities, etc.
"""

from .decl import ProxyState
from .derived import derived_property
from .exceptions import *
from .extras import ExtrasProperty, ExtrasProxy
from .fieldvalidation import *
from .property import Id, NameId, Property
from .proxy import Proxy, deferred_sync
from .proxylist import ProxyCursor, ProxyList, ProxySublist, ProxyVec
from .proxysync import ProxySynclist
from .refs import Reference, RefList
from .registry import Registry, RegistryCatalog
from .schema import Schema
from .tag import TaggableProxy, TagList

__all__ = []

# Include all exceptions
from .exceptions import __all__ as _a

__all__ += _a
del _a

from .fieldvalidation import __all__ as _a

__all__ += _a
del _a

__all__ += [
    "Property",
    "Id",
    "NameId",
    "Reference",
    "RefList",
    "TagList",
    "Schema",
    "Proxy",
    "deferred_sync",
    "ProxyState",
    "ProxyCursor",
    "ProxyList",
    "ProxySublist",
    "ProxyVec",
    "ProxySynclist",
    "ExtrasProperty",
    "ExtrasProxy",
    "TaggableProxy",
    "derived_property",
    "Registry",
    "RegistryCatalog",
]
