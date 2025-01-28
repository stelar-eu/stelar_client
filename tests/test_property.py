from datetime import datetime
from uuid import UUID, uuid4

import pytest
from proxy_utils import ProxyTestObj, TPCatalog

from stelar.client import deferred_sync
from stelar.client.proxy import *
from stelar.client.proxy import (
    BoolField,
    DateField,
    Id,
    IntField,
    InvalidationError,
    Property,
    Proxy,
    ProxyState,
    Schema,
    StrField,
    UUIDField,
)


def test_derived_property():
    class Foo(ProxyTestObj):
        a = Property(validator=IntField, updatable=True)

        @derived_property
        def two_a(self, entity):
            return 2 * entity["a"]

    c = TPCatalog()

    x = Foo.new(c, a=5)
    assert x.a == 5
    assert x.two_a == 10

    x.a = 20
    assert x.two_a == 40

    with deferred_sync(x):
        x.a = 1
        assert x.two_a == 40
    assert x.two_a == 2


def test_inherited_property():
    class Foo(ProxyTestObj, entity=False):
        a = Property(validator=IntField, updatable=True)

    class Bar(Foo):
        b = Property(validator=IntField, updatable=True)

    assert hasattr(Bar, "proxy_schema")
    assert not hasattr(Foo, "proxy_schema")

    assert set(Bar.proxy_schema.properties) == {"a", "b"}
    assert Bar.proxy_schema.abstract_base_classes == [Foo, ProxyTestObj, Proxy]

    c = TPCatalog()

    with pytest.raises(TypeError):
        Foo.new(c, a=1)

    x = Bar.new(c, a=1, b=3)
    assert x.a == 1
    assert x.b == 3
