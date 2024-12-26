from uuid import uuid4
from proxy_utils import TPCache, ProxyTestObj
from stelar_client.proxy import Proxy, Property, Id, Registry, RefList


def test_simple_subset_decl():
    class Foo(ProxyTestObj):
        a = Property()

    class Bar(ProxyTestObj):
        b = Property()
        acoll = RefList(Foo)

    assert 'acoll' in Bar.proxy_schema.properties
    acoll_descriptor = Bar.proxy_schema.properties['acoll']
    assert acoll_descriptor.name == 'acoll'
    assert acoll_descriptor.proxy_type is Foo


def test_collection_init():
    uuids = [uuid4() for i in range(4)]
    class Foo(ProxyTestObj):
        a = Property()

    Foo.data = {
        uuids[i]: {
            'id': uuids[i],
            'a': f'this is a {i}'
        }

        for i in range(3)
    }

    class Bar(ProxyTestObj):
        b = Property()
        acoll = RefList(Foo)

    Bar.data = {
        uuids[3]: {
            'id': uuids[3],
            'b': 'this is b',
            'acoll': [
                Foo.data[u] for u in uuids[:3]
            ]
        }
    }

    foo_cache = TPCache(Foo)
    bar_cache = TPCache(Bar)

    