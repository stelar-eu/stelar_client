from stelar_client.proxy import ProxyObj, ProxyProperty

def test_proxy_obj():
    class Foo(ProxyObj):
        pass

    x = Foo()

    assert x.obj is None

