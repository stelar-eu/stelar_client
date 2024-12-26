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
    ProxyProperty, ProxyId, ProxyReference, ProxySubset
)
from .schema import ProxySchema
from .proxy import ProxyObj, ProxyCache


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

    'ProxyProperty',
    'ProxyId',
    'ProxyReference',
    'ProxySubset',

    'ProxySchema',

    'ProxyObj',
    'ProxyCache',
    'ProxyState',
]