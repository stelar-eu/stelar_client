"""
The STELAR client's proxying package.

The definitions here implement entity proxying by the client.
Entities include Data Catalog entities, authorization entities, etc.
"""

from .decl import ProxyState
from .exceptions import *
from .fieldvalidation import *
from .property import (
    Property, Id, NameId, Reference, RefList
)
from .schema import Schema
from .proxy import Proxy
from .proxylist import ProxyCursor, ProxyList, ProxySublist
from .proxysync import ProxySynclist
from .registry import Registry, RegistryCatalog


__all__ = []

# Include all exceptions
from .exceptions import __all__ as _a
__all__ += _a
del _a

from .fieldvalidation import __all__ as _a
__all__ += _a
del _a

__all__ += [

    'Property',
    'Id',
    'NameId',
    'Reference',
    'RefList',

    'Schema',

    'Proxy',
    'ProxyState',
    'ProxyCursor',
    'ProxyList',
    'ProxySublist',
    'ProxySynclist',

    'Registry',
    'RegistryCatalog',
]