import pytest
from stelar_client.proxy import (Proxy, Property, Id,
                                 Schema, IntField, StrField, DateField, BoolField, UUIDField,
                                 ProxyState, InvalidationError)
from uuid import uuid4, UUID
from datetime import datetime
from proxy_utils import TPCatalog, ProxyTestObj
from stelar_client import deferred_sync
from stelar_client.proxy import *


def test_derived_property():

    class Foo(ProxyTestObj):
        a = Property(validator=IntField, updatable=True)

        @derived_property
        def two_a(self, entity):
            return 2*entity['a']

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





