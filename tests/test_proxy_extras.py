import pytest
from uuid import *
from stelar_client.proxy import *
from proxy_utils import ProxyTestObj, TPCatalog, TPRegistry


def test_extras_proxy():

    class Foo(ProxyTestObj, ExtrasProxy):

        a = Property(validator=IntField, updatable=True)
        b = Property(validator=StrField, updatable=True)
        extras = ExtrasProperty()


    uuids = [uuid4() for i in range(2)]

    Foo.data = {
        uuids[0]: {
            "id": uuids[0],
            "a":10,
            "b":20,
            "extras": []
        },

        uuids[1]: {
            "id": uuids[1],
            "a": 100,
            "b": 200,
            "extras": [
                {"key": "foo", "value": "bar"}
            ]
        }
    }


    c = TPCatalog().registry_for(Foo)

    p = c.fetch_proxy(uuids[0])
    assert p.a == 10
    assert p.b == 20
    assert p.proxy_attr['extras'] == {}

    q = c.fetch_proxy(uuids[1])
    assert q.a == 100
    assert q.b == 200

    assert hasattr(q, 'foo')
    assert q.proxy_attr['extras'] == {'foo': 'bar'}
    assert q.foo == 'bar'

    q.foo = 'baz'
    assert Foo.data[q.id]['extras'] == [{"key":"foo", "value":"baz"}]

    q.fozz = 'bozz'
    assert Foo.data[q.id]['extras'] == [
        {"key":"foo", "value":"baz"},
        {"key": "fozz", "value":"bozz"}
    ]

    p.foo = q.fozz
    assert p.foo == q.fozz

    del q.fozz
    assert not hasattr(q, 'fozz')

    p.a = q.a
    assert p.a == q.a
    assert Foo.data[p.id]['a'] == q.a
    with pytest.raises(AttributeError):
        del q.a
    
    