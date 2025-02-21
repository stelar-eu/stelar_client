import pytest
from proxy_utils import ProxyTestObj, TPCatalog

from stelar.client import deferred_sync
from stelar.client.proxy import IntField, Property, Proxy, ProxyState
from stelar.client.proxy.derived import derived_property
from stelar.client.proxy.property import DictProperty


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


def test_dict_property():
    class Foo(ProxyTestObj):
        a = DictProperty(str, str, updatable=True)
        b = DictProperty(str, int, updatable=True)
        c = DictProperty(int, str, updatable=False)
        d = DictProperty(int, int, nullable=True, updatable=True)

    c = TPCatalog()

    x = Foo.new(c, a={}, b={}, c={5: "low"}, d=None)

    assert x.a == {}
    x.a["high"] = "low"
    assert x.proxy_state is ProxyState.CLEAN
    assert x.a["high"] == "low"

    assert x.b == {}
    x.b["high"] = 1
    assert x.proxy_state is ProxyState.CLEAN
    assert x.b["high"] == 1

    with pytest.raises(ValueError):
        x.a["high"] = 1
    assert x.proxy_state is ProxyState.CLEAN
    assert x.a["high"] == "low"
    assert x.b["high"] == 1

    with pytest.raises(ValueError):
        x.b["high"] = "low"
    assert x.proxy_state is ProxyState.CLEAN
    assert x.a["high"] == "low"
    assert x.b["high"] == 1

    with pytest.raises(ValueError):
        x.a["high"] = None
    assert x.proxy_state is ProxyState.CLEAN

    assert x.c == {5: "low"}
    with pytest.raises(AttributeError):
        x.c[2] = "low"
    with pytest.raises(AttributeError):
        x.c[5] = "high"
    with pytest.raises(AttributeError):
        x.c[2] = None

    assert x.d is None
    x.d = {1: 2}
    assert x.d == {1: 2}
    x.d[4] = 5
    assert x.d == {1: 2, 4: 5}
    x.d = None
    assert x.d is None


def test_dict_property_ops():
    class Foo(ProxyTestObj):
        a = DictProperty(str, str, updatable=True)
        b = DictProperty(str, int, updatable=True)
        c = DictProperty(int, str, updatable=False)
        d = DictProperty(int, int, nullable=True, updatable=True)

    c = TPCatalog()

    x = Foo.new(
        c,
        a={"a" + k: k for k in "abc"},
        b={u: ord(u) for u in "abcdefg"},
        c={n: f"v{n}" for n in range(3)},
        d=None,
    )

    # clear get iter pop update setdefault
    assert x.a.get("a") is None
    assert x.a.get("a", "default") == "default"
    assert x.a.get("aa", 5) == "a"
    assert x.a.get("ac") == "c"
    assert len(x.a) == 3
    assert list(x.a) == ["aa", "ab", "ac"]
    assert list(x.a.keys()) == ["aa", "ab", "ac"]
    assert list(x.a.values()) == ["a", "b", "c"]
    assert list(x.a.items()) == [("aa", "a"), ("ab", "b"), ("ac", "c")]
    assert x.a.pop("ab") == "b"
    assert "ab" not in x.a
    assert x.a.setdefault("ab", "b") == "b"
    assert x.a.setdefault("ab", "c") == "b"
    x.a.update({"ab": "b", "ac": "c"})
    assert x.a == {"aa": "a", "ab": "b", "ac": "c"}
    x.a.clear()
    assert x.a == {}

    assert x.b == {"a": 97, "b": 98, "c": 99, "d": 100, "e": 101, "f": 102, "g": 103}
    assert x.b.get("a") == 97
    assert x.b.get("z") is None
    assert x.b.get("z", 5) == 5
    assert len(x.b) == 7

    assert x.c == {0: "v0", 1: "v1", 2: "v2"}
    for k in range(3):
        assert x.c[k] == f"v{k}"
        assert k in x.c
    assert 3 not in x.c
    assert len(x.c) == 3
    for k, i in enumerate(sorted(x.c)):
        assert k == i
