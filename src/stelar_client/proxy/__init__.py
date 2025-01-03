"""
The STELAR client's proxying package.

The definitions here implement entity proxying by the client.
Entities include Data Catalog entities, authorization entities, etc.
"""

from .decl import ProxyState
from .exceptions import EntityError, ProxyError, InvalidationError, ConflictError, ProxyOperationError
from .fieldvalidation import (
    AnyField, BoolField, IntField, StrField, DateField, UUIDField, NameField
)
from .property import (
    Property, Id, NameId, Reference, RefList
)
from .schema import Schema
from .proxy import Proxy
from .proxylist import ProxyCursor, ProxyList, ProxySublist
from .proxysync import ProxySynclist
from .registry import Registry, RegistryCatalog

__all__ = [
    'EntityError',
    'ProxyError',
    'InvalidationError',
    'ConflictError',
    'ProxyOperationError',

    'AnyField',
    'BoolField',
    'IntField',
    'StrField',
    'DateField',
    'UUIDField',
    'NameField',

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