import pytest
from stelar_client.proxy import Registry, RegistryCatalog, Proxy, Property
from proxy_utils import ProxyTestObj

def test_create_catalog():
    
    class Foo(ProxyTestObj):
        a = Property()
        data = {
            'a': 0
        }

    class Bar(ProxyTestObj):
        a = Property()
        data = {
            'a': 0
        }

    c = RegistryCatalog()
    rFoo = Registry(c, Foo)

    assert c.registry_for(Foo) is rFoo
    with pytest.raises(KeyError):
        c.registry_for(Bar)

    