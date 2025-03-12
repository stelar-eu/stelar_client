from uuid import uuid4

import pytest
from proxy_utils import ProxyTestObj, TPCatalog

from stelar.client.proxy import (
    ExtrasProperty,
    ExtrasProxy,
    IntField,
    Property,
    StrField,
)


def test_extras_proxy():
    class Foo(ProxyTestObj, ExtrasProxy):
        a = Property(validator=IntField, updatable=True)
        b = Property(validator=StrField, updatable=True)
        extras = ExtrasProperty()

    uuids = [uuid4() for i in range(2)]

    Foo.data = {
        uuids[0]: {"id": str(uuids[0]), "a": 10, "b": 20, "extras": {}},
        uuids[1]: {
            "id": str(uuids[1]),
            "a": 100,
            "b": 200,
            "extras": {"foo": "bar"},
        },
    }

    c = TPCatalog().registry_for(Foo)

    p = c.fetch_proxy(uuids[0])
    assert p.a == 10
    assert p.b == 20
    assert p.proxy_attr["extras"] == {}

    q = c.fetch_proxy(uuids[1])
    assert q.foo == "bar"
    assert q.a == 100
    assert q.b == 200

    assert hasattr(q, "foo")
    assert q.proxy_attr["extras"] == {"foo": "bar"}
    assert q.foo == "bar"

    q.foo = "baz"
    assert Foo.data[q.id]["extras"] == {"foo": "baz"}

    q.fozz = "bozz"
    assert Foo.data[q.id]["extras"] == {"foo": "baz", "fozz": "bozz"}

    assert q.extras == {"foo": "baz", "fozz": "bozz"}
    assert q.extras is not q.proxy_attr["extras"]

    p.foo = q.fozz
    assert p.foo == q.fozz

    del q.fozz
    assert not hasattr(q, "fozz")

    p.a = q.a
    assert p.a == q.a
    assert Foo.data[p.id]["a"] == q.a
    with pytest.raises(AttributeError):
        del q.a


def test_extras_create():
    class Foo(ProxyTestObj, ExtrasProxy):
        a = Property(validator=IntField, updatable=True)
        b = Property(validator=StrField, updatable=True)
        extras = ExtrasProperty()

    uuids = [uuid4() for i in range(3)]
    Foo.data = {
        uuids[0]: {"id": str(uuids[0]), "a": 10, "b": "b20", "extras": []},
        uuids[1]: {
            "id": str(uuids[1]),
            "a": 100,
            "b": "b200",
            "extras": [{"key": "foo", "value": "bar"}],
        },
    }

    c = TPCatalog().registry_for(Foo)

    Foo.data[uuids[2]] = Foo.new_entity(a=5, b="hello", skey="sval", ukey="uval")

    assert Foo.data[uuids[2]]["a"] == 5
    assert Foo.data[uuids[2]]["b"] == "hello"
    assert Foo.data[uuids[2]]["extras"] == {"skey": "sval", "ukey": "uval"}

    p = c.fetch_proxy(uuids[2])

    assert p.a == 5
    assert p.b == "hello"
    assert p.skey == "sval"
    assert p.ukey == "uval"


def test_extras_proxy_creation():
    class Foo(ProxyTestObj, ExtrasProxy):
        a = Property(validator=IntField(nullable=False, default=0), updatable=True)
        b = Property(validator=StrField(nullable=True), updatable=True)
        extras = ExtrasProperty()

    c = TPCatalog()

    x = Foo.new(c)
    assert x.a == 0
    assert x.b is None
    assert x.extras == {}

    x = Foo.new(c, a=10, hehe="hihi")
    assert x.a == 10
    assert x.b is None
    assert x.hehe == "hihi"
    assert x.extras == {"hehe": "hihi"}

    x.proxy_invalidate()
    assert x.a == 10
    assert x.b is None
    assert x.hehe == "hihi"
    assert x.extras == {"hehe": "hihi"}
