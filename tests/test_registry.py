import pytest
from proxy_utils import ProxyTestObj

from stelar.client.proxy import Property, Proxy, Registry, RegistryCatalog


def test_create_catalog():
    class Foo(ProxyTestObj):
        a = Property()
        data = {"a": 0}

    class Bar(ProxyTestObj):
        a = Property()
        data = {"a": 0}

    c = RegistryCatalog()
    rFoo = Registry(c, Foo)

    assert c.registry_for(Foo) is rFoo
    with pytest.raises(KeyError):
        c.registry_for(Bar)
