from datetime import datetime
from uuid import UUID, uuid4

import pytest
from proxy_utils import ProxyTestObj, TPCatalog

from stelar.client import deferred_sync
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


##################################################
#  An 'abstract' subclass of Proxy which does
#  not implement an entity.
##################################################
class TestProxy(Proxy, entity=False):
    __test__ = False

    data = {}

    def proxy_sync(self, entity=None):
        if self.proxy_changed is not None:
            entity = self.data = self.proxy_to_entity()
            self.patch = self.proxy_to_entity(self.proxy_changed)
        if entity is None:
            entity = self.data
        self.proxy_from_entity(entity)
        self.proxy_changed = None


def test_abstract():
    class Foo(Proxy, entity=False):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    class Bar(Foo, entity=False):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    class Baz(Bar):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        a = Property()

        def proxy_sync(self):
            self.proxy_attr = {"a": None}
            self.proxy_changed = None

    assert not hasattr(Foo, "proxy_schema")
    assert not hasattr(Bar, "proxy_schema")
    assert hasattr(Baz, "proxy_schema")

    catalog = TPCatalog()
    PFoo = catalog.registry_for(Foo)
    PBar = catalog.registry_for(Bar)
    PBaz = catalog.registry_for(Baz)

    x = PFoo.fetch()
    assert not hasattr(x, "id")

    x = PBar.fetch()
    assert not hasattr(x, "id")

    x = PBaz.fetch()
    assert hasattr(x, "id")
    assert hasattr(x, "a")

    with pytest.raises(TypeError):

        class Bad(Baz):
            a = Property()


def test_non_entity_class_property_raises():
    with pytest.raises((RuntimeError, TypeError)):

        class Foo:
            a = Property()

    with pytest.raises((RuntimeError, TypeError)):

        class Foo2:
            a = Id()


def test_proxy_schema_registration():
    class Foo(Proxy):
        pass

    assert hasattr(Foo, "proxy_schema")
    assert Schema.for_entity("Foo") is Foo.proxy_schema


def test_empty_proxy_obj_schema():
    class Foo(Proxy):
        pass

    PFoo = TPCatalog().registry_for(Foo)
    eid = uuid4()
    x = PFoo.fetch(eid)

    #
    assert x.proxy_attr is None
    assert len(x.proxy_schema.properties) == 0
    assert x.proxy_schema.id.name == "id"
    assert x.id == eid


def test_empty_proxy_obj_given_key():
    class Foo(Proxy):
        myid = Id()

    eid = uuid4()
    x = TPCatalog().registry_for(Foo).fetch(eid)

    #
    assert x.proxy_attr is None
    assert len(x.proxy_schema.properties) == 0
    assert x.proxy_schema.id.name == "myid"
    assert x.proxy_schema.id.entity_name == "myid"
    assert x.myid == eid


def test_empty_proxy_obj_given_key_with_args():
    class Foo(Proxy):
        myid = Id(entity_name="entity_id", doc="The ID doc")

    eid = uuid4()
    x = TPCatalog().registry_for(Foo).fetch(eid)

    #
    assert x.proxy_attr is None
    assert len(x.proxy_schema.properties) == 0
    assert x.proxy_schema.id.name == "myid"
    assert x.myid == eid
    assert x.proxy_schema.id.entity_name == "entity_id"
    assert "The ID doc" in x.proxy_schema.id.__doc__


def test_property():
    class Foo(Proxy):
        aprop = Property()

    eid = uuid4()
    x = TPCatalog().registry_for(Foo).fetch(eid)

    # Just checking...
    assert x.proxy_attr is None
    assert len(x.proxy_schema.properties) == 1
    assert x.proxy_schema.id.name == "id"
    assert x.id == eid

    p = x.proxy_schema.properties["aprop"]
    assert p.name == "aprop"
    assert p.updatable is False
    assert p.optional is False
    assert p.entity_name == "aprop"


def test_proxy_obj():
    class Foo(Proxy):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.data = {
                "a": 10,
                "b": "Hello",
                "c": None,
            }

        a = Property(updatable=True)
        b = Property(updatable=True)
        c = Property(updatable=True)

        def proxy_sync(self, entity=None):
            if self.proxy_changed is not None:
                entity = self.data = self.proxy_to_entity()
                self.proxy_changed = None
            if entity is None:
                entity = self.data
            self.proxy_from_entity(entity)

    eid = uuid4()
    x = TPCatalog().registry_for(Foo).fetch(eid)

    assert x.proxy_attr is None
    assert x.proxy_state is ProxyState.EMPTY
    assert len(x.proxy_schema.properties) == 3
    assert x.proxy_schema.id.name == "id"
    assert x.id == eid
    assert x.proxy_attr is None
    assert x.proxy_changed is None

    assert x.a == 10
    assert x.b == "Hello"
    assert x.c is None
    assert x.proxy_changed is None
    assert x.proxy_state is ProxyState.CLEAN

    x.proxy_autosync = False
    x.a = 20
    x.b = "Hi there"
    assert x.proxy_changed is not None
    assert x.proxy_state is ProxyState.DIRTY
    x.proxy_sync()
    assert x.proxy_state is ProxyState.CLEAN

    assert x.a == 20
    assert x.b == "Hi there"
    assert x.proxy_changed is None
    assert x.proxy_state is ProxyState.CLEAN

    x.a = 30
    assert x.proxy_state is ProxyState.DIRTY
    assert x.a == 30
    with pytest.raises(InvalidationError):
        x.proxy_invalidate()
    x.proxy_reset()
    assert x.proxy_state is ProxyState.CLEAN
    assert x.a == 20
    assert x.b == "Hi there"

    x.a = 30
    assert x.proxy_state is ProxyState.DIRTY
    assert x.a == 30
    x.proxy_invalidate(force=True)
    assert x.proxy_state is ProxyState.EMPTY
    assert x.a == 20
    assert x.proxy_state is ProxyState.CLEAN


def test_attr_read_only():
    class Foo(TestProxy):
        a = Property(updatable=False)
        data = {"a": 20}

    eid = uuid4()
    x = TPCatalog().registry_for(Foo).fetch(eid)

    assert x.a == 20
    with pytest.raises(expected_exception=AttributeError):
        x.a = 10

    with pytest.raises(expected_exception=AttributeError):
        del x.a

    y = TPCatalog().registry_for(Foo).fetch()
    with pytest.raises(expected_exception=AttributeError):
        y.a = 10

    with pytest.raises(expected_exception=AttributeError):
        del y.a

    assert x.a == 20
    assert y.a == 20


def test_prop_optional():
    class Foo(TestProxy):
        c = Property(updatable=True)
        a = Property(optional=True, updatable=True)
        b = Property(optional=True, updatable=False)

        data = {}

    eid = uuid4()
    x = TPCatalog().registry_for(Foo).fetch(eid)
    with pytest.raises(ValueError):
        x.c

    x.data = {"c": 10}
    x.proxy_invalidate()
    assert x.c == 10
    assert not hasattr(x, "a")
    assert not hasattr(x, "b")

    x.proxy_autosync = False
    x.a = 10
    assert x.a == 10
    assert hasattr(x, "a")
    assert not hasattr(x, "b")

    assert "a" not in x.data
    x.proxy_sync()
    assert x.data["a"] == 10

    with pytest.raises(AttributeError):
        x.b = 20  # this fails because b is not updatable

    x.data["b"] = 20
    x.proxy_sync()
    assert x.b == 20
    del x.b
    assert not hasattr(x, "b")
    x.proxy_sync()
    assert "b" not in x.data


def test_property_validator():
    class Foo(TestProxy):
        a = Property(validator=IntField, updatable=True)
        b = Property(validator=StrField(), updatable=False)
        data = {"a": -1, "b": "one"}

    assert Foo.proxy_schema.properties["a"].validator.validate(10) == 10
    assert Foo.proxy_schema.properties["b"].validator.validate("10") == "10"

    x = TPCatalog().registry_for(Foo).fetch()
    assert x.a == -1
    x.a = 10
    assert x.a == 10


def test_missing_values():
    class Foo(TestProxy):
        a = Property(updatable=True)
        b = Property(updatable=False)
        data = {}

    x = TPCatalog().registry_for(Foo).fetch()
    with pytest.raises(ValueError):
        x.a

    x.data = {"a": 10, "b": 20}
    x.proxy_invalidate()
    assert x.a == 10
    assert x.b == 20


def test_set_changed_once():
    class Foo(TestProxy):
        a = Property(updatable=True)
        data = {"a": 1}

    x = TPCatalog().registry_for(Foo).fetch()
    x.proxy_autosync = False
    assert x.a == 1
    x.a = 2
    assert x.a == 2
    x.a = 3
    assert x.a == 3

    assert x.proxy_attr["a"] == 3
    assert x.proxy_changed["a"] == 1

    x.proxy_reset()
    assert x.a == 1


def test_multiple_keys_raise():
    with pytest.raises(TypeError):

        class Foo(TestProxy):
            id1 = Id()
            id2 = Id()


def test_id_property_nonkey_raise():
    with pytest.raises(TypeError):

        class Foo(TestProxy):
            id = Property()

        # This should raise
        TPCatalog().registry_for(Foo).fetch()


def test_Proxy_init():
    class Foo(TestProxy):
        a = Property()
        data = {"a": 1}

    eid = uuid4()
    eid2 = uuid4()
    tpc = TPCatalog().registry_for(Foo)

    with pytest.raises(ValueError):
        x = Foo(tpc)

    with pytest.raises(ValueError):
        x = Foo(tpc, eid=eid, entity={"id": str(eid2), "a": 10})

    with pytest.raises(ValueError):
        x = Foo(tpc, entity={"id2": str(eid2), "a": 10})

    x = Foo(tpc, eid, entity={"id": str(eid), "a": 20})
    assert x.id == eid

    x = Foo(tpc, eid, entity={"a": 30})
    assert x.id == eid
    assert x.a == 1

    x = Foo(tpc, eid)
    assert x.id == eid

    x = Foo(tpc, str(eid))
    assert x.id == eid
    assert x.a == 1

    x = Foo(tpc, entity={"id": eid, "a": 20})
    assert x.a == 1


def test_setting_on_new_obj_syncs():
    class Foo(TestProxy):
        a = Property(updatable=True)
        b = Property(updatable=True)
        data = {"a": 10, "b": 20}

    x = TPCatalog().registry_for(Foo).fetch()
    assert x.proxy_attr is None
    x.a = 1
    assert x.proxy_attr["a"] == 1
    assert x.proxy_attr["b"] == 20


def test_cannot_set_to_ellipsis():
    class Foo(TestProxy):
        a = Property(updatable=True)
        b = Property(updatable=True)
        data = {"a": 10, "b": 20}

    x = TPCatalog().registry_for(Foo).fetch()
    assert x.proxy_attr is None
    x.proxy_sync()

    with pytest.raises(ValueError):
        x.a = ...


def test_double_deletion():
    class Foo(TestProxy):
        a = Property(updatable=True)
        b = Property(updatable=True, optional=True)
        data = {"a": 10, "b": 20}

    x = TPCatalog().registry_for(Foo).fetch()
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
        a = Property(updatable=True)
        b = Property(updatable=True, optional=True)
        data = {"a": 10, "b": 20}

    eid = uuid4()
    x = TPCatalog().registry_for(Foo).fetch(eid)
    assert x.id == eid
    with pytest.raises(AttributeError):
        x.id = uuid4()

    with pytest.raises(AttributeError):
        del x.id


def test_autosync():
    class Foo(TestProxy):
        a = Property(updatable=True)
        b = Property(updatable=True, optional=True)
        data = {"a": 10, "b": 20}

    eid = uuid4()
    x = TPCatalog().registry_for(Foo).fetch(eid)

    assert x.proxy_autosync

    x.a = 4
    assert x.a == 4
    assert x.data["a"] == 4

    x.update(a=0, b="haha")
    assert x.a == 0
    assert x.b == "haha"
    assert x.data == {"a": 0, "b": "haha"}

    x.update(a=100, b=...)
    assert x.a == 100
    assert not hasattr(x, "b")
    assert x.data == {"a": 100}


def test_autosync2():
    class Foo(TestProxy):
        a = Property(validator=IntField, updatable=True, optional=True)
        b = Property(validator=IntField, updatable=True, optional=True)
        data = {"a": 10, "b": 20}

    eid = uuid4()
    x = TPCatalog().registry_for(Foo).fetch(eid)

    assert x.proxy_autosync
    with pytest.raises(ValueError):
        x.a = "aa"
    assert x.a == 10
    assert x.b == 20

    with pytest.raises(ValueError):
        x.update(a=0, b="aa")
    assert x.a == 10
    assert x.b == 20

    with pytest.raises(ValueError):
        x.update(a="aa", b=0)
    assert x.a == 10
    assert x.b == 20

    with pytest.raises(ValueError):
        x.update(a=20, b="aa")
    assert x.a == 10
    assert x.b == 20


def test_proxy_new():
    class Foo(ProxyTestObj):
        a = Property(validator=IntField, updatable=True, optional=True)
        b = Property(validator=StrField(default="world"), updatable=True, optional=True)
        c = Property(validator=BoolField(default=True), updatable=True, optional=True)
        d = Property(validator=DateField, updatable=True, optional=True)
        e = Property(
            validator=UUIDField(default=uuid4()), updatable=True, optional=True
        )

        data = {}

    uu = uuid4()
    Foo.data[uu] = Foo.new_entity(
        a=10, b="hello", c=False, d=datetime(2005, 9, 18, 23, 55), e=uu
    )

    assert Foo.data[uu]["a"] == 10
    assert Foo.data[uu]["b"] == "hello"
    assert Foo.data[uu]["c"] is False
    assert Foo.data[uu]["d"] == datetime(2005, 9, 18, 23, 55).isoformat()
    assert Foo.data[uu]["e"] == str(uu)

    c = TPCatalog()
    x = c.registry_for(Foo).fetch(uu)

    assert x.a == 10
    assert x.b == "hello"
    assert x.c is False
    assert x.d == datetime(2005, 9, 18, 23, 55)
    assert x.e == uu

    dnow = datetime.now()
    y = Foo.new(c, a=25, b="vsam", c=True, d=dnow, e=uu)

    assert y.id != UUID(int=0)
    assert y.a == 25
    assert y.b == "vsam"
    assert y.c is True
    assert y.d == dnow
    assert y.e == uu

    y.proxy_invalidate()
    assert y.proxy_state is ProxyState.EMPTY

    # Reloads
    assert y.a == 25
    assert y.b == "vsam"
    assert y.c is True
    assert y.d == dnow
    assert y.e == uu

    z = Foo.new(c, a=25, autosync=False)
    assert z.id == UUID(int=0)
    assert z.a == 25
    assert z.proxy_state is ProxyState.DIRTY

    with pytest.raises(NotImplementedError):
        z.proxy_sync()

    assert z.proxy_autosync

    with deferred_sync(z):
        assert z.id == UUID(int=0)
        z.d = dnow
        assert z.id == UUID(int=0)

    assert z.id != UUID(int=0)
    assert z.proxy_state is ProxyState.CLEAN
