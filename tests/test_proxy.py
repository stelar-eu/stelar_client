import pytest
from stelar_client.proxy import ProxyObj, ProxyProperty, ProxyId, ProxyCache, ProxySchema
from uuid import uuid4

class TPCache(ProxyCache):
    def __init__(self, proxy_type):
        super().__init__(None, proxy_type)
    def fetch(self, eid=None):
        if eid is None:
            eid = uuid4()
        return self.proxy_type(self, eid)


def test_abstract():
    class Foo(ProxyObj, entity=False):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    class Bar(Foo, entity=False):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    class Baz(Bar):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        a = ProxyProperty()
        def proxy_fetch(self):
            return {'a': None}

    assert not hasattr(Foo, 'proxy_schema')
    assert not hasattr(Bar, 'proxy_schema')
    assert hasattr(Baz, 'proxy_schema')

    PFoo = TPCache(Foo)
    PBar = TPCache(Bar)
    PBaz = TPCache(Baz)

    x = PFoo.fetch()
    assert not hasattr(x, 'id')

    x = PBar.fetch()
    assert not hasattr(x, 'id')

    x = PBaz.fetch()
    assert hasattr(x, 'id')
    assert hasattr(x, 'a')
    
    with pytest.raises(TypeError):
        class Bad(Bar, entity=False):
            a = ProxyProperty()


def test_non_entity_class_property_raises():
    with pytest.raises((RuntimeError, TypeError)):
        class Foo:
            a = ProxyProperty()

    with pytest.raises((RuntimeError, TypeError)):
        class Foo:
            a = ProxyId()

    with pytest.raises(TypeError):
        class Foo(ProxyObj, entity=False):
            a = ProxyId()

    with pytest.raises(TypeError):
        class Foo(ProxyObj, entity=False):
            a = ProxyProperty()



def test_proxy_schema_registration():
    class Foo(ProxyObj):
        pass

    assert hasattr(Foo, 'proxy_schema')
    assert ProxySchema.for_entity('Foo') is Foo.proxy_schema

def test_empty_proxy_obj_schema():
    class Foo(ProxyObj):
        pass

    PFoo = TPCache(Foo)
    eid = uuid4()
    x = PFoo.fetch(eid)
    
    # 
    assert x.proxy_attr is None
    assert len(x.proxy_schema.properties) == 0
    assert x.proxy_schema.id.name == 'id'
    assert x.id == eid 


def test_empty_proxy_obj_given_key():

    class Foo(ProxyObj):
        myid = ProxyId()

    eid = uuid4()
    x = TPCache(Foo).fetch(eid)

    # 
    assert x.proxy_attr is None
    assert len(x.proxy_schema.properties) == 0
    assert x.proxy_schema.id.name == 'myid'
    assert x.proxy_schema.id.entity_name == 'myid'
    assert x.myid == eid 

def test_empty_proxy_obj_given_key_with_args():
    class Foo(ProxyObj):
        myid = ProxyId(entity_name='entity_id', doc="The ID doc")

    eid = uuid4()
    x = TPCache(Foo).fetch(eid)

    # 
    assert x.proxy_attr is None
    assert len(x.proxy_schema.properties) == 0
    assert x.proxy_schema.id.name == 'myid'
    assert x.myid == eid 
    assert x.proxy_schema.id.entity_name == 'entity_id'
    assert x.proxy_schema.id.__doc__ == 'The ID doc'



def test_property():

    class Foo(ProxyObj):
        aprop = ProxyProperty()

    eid = uuid4()
    x = TPCache(Foo).fetch(eid)

    # Just checking...
    assert x.proxy_attr is None
    assert len(x.proxy_schema.properties) == 1
    assert x.proxy_schema.id.name == 'id'
    assert x.id == eid 

    p = x.proxy_schema.properties['aprop']
    assert p.name == 'aprop'
    assert p.updatable is False
    assert p.optional is False
    assert p.entity_name == 'aprop'


##################################################
#  An 'abstract' subclass of ProxyObj which does
#  not implement an entity.
##################################################
class TestProxy(ProxyObj, entity=False):
    __test__ = False

    data = {}
    def proxy_fetch(self):
        return self.data
    def proxy_update(self, new_data, old_data):
        self.data = new_data
        self.old_data = old_data
        return new_data




def test_proxy_obj():
    class Foo(ProxyObj):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.data = {
                'a': 10,
                'b': "Hello",
                'c': None,
            }

        a = ProxyProperty(updatable=True)
        b = ProxyProperty(updatable=True)
        c = ProxyProperty(updatable=True)

        def proxy_fetch(self):
            return self.data
        def proxy_update(self, new_data, old_data):
            self.data = new_data
            return new_data

    eid = uuid4()
    x = TPCache(Foo).fetch(eid)
    assert x.proxy_attr is None
    assert len(x.proxy_schema.properties) == 3
    assert x.proxy_schema.id.name == 'id'
    assert x.id == eid 
    assert x.proxy_attr is None
    assert x.proxy_clean()

    assert x.a == 10
    assert x.b == "Hello"
    assert x.c is None
    assert x.proxy_clean()

    x.a = 20
    x.b = "Hi there"    
    assert not x.proxy_clean()
    x.proxy_sync()

    assert x.a == 20
    assert x.b == "Hi there"
    assert x.proxy_clean()


def test_attr_read_only():

    class Foo(TestProxy):
        a = ProxyProperty(updatable=False)
        data = {'a': 20}

    eid = uuid4()
    x = TPCache(Foo).fetch(eid)

    assert x.a == 20
    with pytest.raises(expected_exception=AttributeError):
        x.a = 10

    with pytest.raises(expected_exception=AttributeError):
        del x.a
      
    y = TPCache(Foo).fetch()
    with pytest.raises(expected_exception=AttributeError):
        y.a = 10

    with pytest.raises(expected_exception=AttributeError):
        del y.a
    
    assert x.a == 20
    assert y.a == 20


def test_prop_optional():
    class Foo(TestProxy):
        c = ProxyProperty(updatable=True)
        a = ProxyProperty(optional=True, updatable=True)
        b = ProxyProperty(optional=True, updatable=False)

        data = {}

    eid = uuid4()
    x = TPCache(Foo).fetch(eid)
    with pytest.raises(ValueError):
        x.c

    x.data = {'c': 10}
    assert x.c == 10
    assert not hasattr(x, 'a')
    assert not hasattr(x, 'b')

    x.a = 10
    assert x.a == 10
    assert hasattr(x, 'a')
    assert not hasattr(x, 'b')

    assert 'a' not in x.data
    x.proxy_sync()
    assert x.data['a'] == 10

    with pytest.raises(AttributeError):
        x.b = 20  # this fails because b is not updatable

    x.data['b'] = 20
    x.proxy_sync()
    assert x.b == 20
    del x.b
    assert not hasattr(x,'b')
    x.proxy_sync()
    assert 'b' not in x.data


def test_missing_values():
    class Foo(TestProxy):
        a = ProxyProperty(updatable=True)
        b = ProxyProperty(updatable=False)
        data = {}


    x = TPCache(Foo).fetch()
    with pytest.raises(ValueError):
        x.a

    x.data = {'a':10, 'b': 20}
    assert x.a == 10
    assert x.b == 20


def test_set_changed_once():
    class Foo(TestProxy):
        a = ProxyProperty(updatable=True)
        data = {'a': 1}

    
    x = TPCache(Foo).fetch()
    assert x.a == 1
    x.a = 2
    assert x.a == 2
    x.a = 3
    assert x.a == 3

    assert x.data['a'] == 1
    assert not hasattr(x, 'old_data')
    x.proxy_sync()
    assert x.old_data['a'] == 1
    assert x.data['a'] == 3


def test_multiple_keys_raise():
    with pytest.raises(TypeError): 
        class Foo(TestProxy):
            id1 = ProxyId()
            id2 = ProxyId()

def test_id_property_nonkey_raise():
    with pytest.raises(TypeError): 
        class Foo(TestProxy):
            id = ProxyProperty()
        x = TPCache(Foo).fetch()


def test_proxyobj_init():
    class Foo(TestProxy):
        a = ProxyProperty()
        data = {'a': 1}

    eid = uuid4()
    eid2 = uuid4()
    tpc = TPCache(Foo)

    with pytest.raises(ValueError):
        x = Foo(tpc)

    with pytest.raises(ValueError):
        x = Foo(tpc, eid=eid, entity={'id': str(eid2), 'a': 10})

    with pytest.raises(ValueError):
        x = Foo(tpc, entity = {'id2': str(eid2), 'a': 10})

    x = Foo(tpc, eid, entity={'id': str(eid), 'a': 20})
    assert x.id == eid

    x = Foo(tpc, eid, entity={'a': 30})
    assert x.id == eid
    assert x.a == 30

    x = Foo(tpc, eid)
    assert x.id == eid

    x = Foo(tpc, str(eid))
    assert x.id == eid
    assert x.a == 1

    x = Foo(tpc, entity={'id': eid, 'a': 20})
    assert x.a == 20


def test_setting_on_new_obj_syncs():
    class Foo(TestProxy):
        a = ProxyProperty(updatable=True)
        b = ProxyProperty(updatable=True)
        data = {'a': 10, 'b':20}

    x = TPCache(Foo).fetch()
    assert x.proxy_attr is None
    x.a = 1
    assert x.proxy_attr['a'] == 1
    assert x.proxy_attr['b'] == 20


def test_cannot_set_to_ellipsis():
    class Foo(TestProxy):
        a = ProxyProperty(updatable=True)
        b = ProxyProperty(updatable=True)
        data = {'a': 10, 'b':20}

    x = TPCache(Foo).fetch()
    assert x.proxy_attr is None
    x.proxy_sync()

    with pytest.raises(ValueError):
        x.a = ...


def test_double_deletion():
    class Foo(TestProxy):
        a = ProxyProperty(updatable=True)
        b = ProxyProperty(updatable=True, optional=True)
        data = {'a': 10, 'b':20}

    x = TPCache(Foo).fetch()
    assert x.proxy_attr is None
    x.proxy_sync()

    del x.b
    with pytest.raises(AttributeError):
        del x.b

    x.proxy_sync()
    with pytest.raises(AttributeError):
        del x.b


def test_key_unchangable():
    class Foo(TestProxy):
        a = ProxyProperty(updatable=True)
        b = ProxyProperty(updatable=True, optional=True)
        data = {'a': 10, 'b':20}

    eid = uuid4()
    x = TPCache(Foo).fetch(eid)
    assert x.id == eid
    with pytest.raises(AttributeError):
        x.id = uuid4()

    with pytest.raises(AttributeError):
        del x.id
