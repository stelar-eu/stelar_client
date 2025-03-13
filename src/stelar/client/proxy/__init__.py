"""
The STELAR client's proxying package.

The definitions here implement entity proxying by the client.
Entities include Data Catalog entities, authorization entities, etc.
"""

from .decl import ProxyState
from .derived import derived_property
from .exceptions import *  # noqa
from .exceptions import __all__ as __all_exceptions__
from .extras import ExtrasProperty, ExtrasProxy
from .fieldvalidation import *  # noqa
from .fieldvalidation import __all__ as __all_fieldvalidation__
from .property import Id, NameId, Property
from .proxy import Proxy, deferred_sync
from .proxycursor import ProxyCursor
from .proxylist import ProxyList, ProxySublist, ProxyVec
from .proxysync import ProxySynclist
from .refs import Reference, RefList
from .registry import Registry, RegistryCatalog
from .schema import Schema
from .tag import TaggableProxy, TagList

__all__ = [
    *__all_exceptions__,
    *__all_fieldvalidation__,
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

del __all_exceptions__
del __all_fieldvalidation__

import os

if os.getenv("SPHINX_BUILD"):
    # This prevents duplicate documentation by sphinx
    del __all__
