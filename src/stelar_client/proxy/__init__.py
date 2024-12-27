"""
The STELAR client's proxying package.

The definitions here implement entity proxying by the client.
Entities include Data Catalog entities, authorization entities, etc.
"""

from .decl import ProxyState
from .exceptions import EntityError, ProxyError, InvalidationError
from .fieldvalidation import (
    AnyField, BoolField, IntField, StrField, DateField, UUIDField
)
from .property import (
    Property, Id, Reference, RefList
)
from .schema import Schema
from .proxy import Proxy
from .registry import Registry, RegistryCatalog

__all__ = [
    'EntityError',
    'ProxyError',
    'InvalidationError',

    'AnyField',
    'BoolField',
    'IntField',
    'StrField',
    'DateField',
    'UUIDField',

    'Property',
    'Id',
    'Reference',
    'RefList',

    'Schema',

    'Proxy',
    'ProxyState',

    'Registry',
    'RegistryCatalog',
]