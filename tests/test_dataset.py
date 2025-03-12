import pytest

from stelar.client import ErrorState, ProxyState


def test_dataset_create(testcli):
    c = testcli

    d = c.datasets.create(name="test_dataset_create", title="A test")
    assert d.title == "A test"

    d.proxy_invalidate()
    assert d.title == "A test"

    d.delete(purge=True)
    assert d.proxy_state is ProxyState.ERROR


def test_dataset_cursor_not_found(testcli):
    c = testcli

    with pytest.raises(KeyError):
        d = c.datasets["test_not_found"]

    d = c.datasets.create(name="test_not_found")
    assert c.datasets["test_not_found"] is d
    assert c.datasets[d.id] is d


def test_dataset_add_resources(testcli):
    c = testcli

    d = c.datasets.create(name="test_dataset_add_resources")
    r1 = c.resources.create(dataset=d, name="my name")
    r2 = c.resources.create(dataset=d, name="my name")

    assert r1.dataset is d
    assert r1.name == "my name"

    assert r2.dataset is d
    assert r2.name == "my name"


def test_dataset_remove_resources(testcli):
    c = testcli

    d = c.datasets.create(name="test_dataset_add_resources")
    r1 = c.resources.create(dataset=d, name="my name")
    r2 = c.resources.create(dataset=d, name="my name")

    assert r1.dataset is d
    assert r1.name == "my name"

    assert r2.dataset is d
    assert r2.name == "my name"

    assert d.resources == [r1, r2]
    r1.delete()
    assert d.resources == [r2]
    r2.delete()
    assert d.resources == []


def test_dataset_delete(testcli):
    c = testcli

    d = c.datasets.create(name="test_dataset_add_resources")
    r1 = c.resources.create(dataset=d, name="my name")
    r2 = c.resources.create(dataset=d, name="my name")

    assert r1.dataset is d
    assert r1.name == "my name"

    assert r2.dataset is d
    assert r2.name == "my name"

    d.delete()
    assert d.state == "deleted"

    assert r1.dataset is d
    assert r2.dataset is d


def test_dataset_purge(testcli):
    c = testcli

    d = c.datasets.create(name="test_dataset_add_resources")
    r1 = c.resources.create(dataset=d, name="my name")
    r2 = c.resources.create(dataset=d, name="my name")

    assert r1.dataset is d
    assert r1.name == "my name"

    assert r2.dataset is d
    assert r2.name == "my name"

    d.delete(purge=True)
    assert d.proxy_state is ProxyState.ERROR
    with pytest.raises(ErrorState):
        d.proxy_sync()
    with pytest.raises(ErrorState):
        d.title
    with pytest.raises(ErrorState):
        d.proxy_reset()
    with pytest.raises(ErrorState):
        d.proxy_invalidate()

    assert r1.proxy_state is ProxyState.ERROR
    assert r2.proxy_state is ProxyState.ERROR


def test_dataset_add_resource(testcli):
    c = testcli

    d = c.datasets.create(name="test_dataset_add_resources")
    r1 = d.add_resource(name="my name")

    # With more attributes and an extra field
    r2 = d.add_resource(name="my name also", url="http://foo", foo="bar")

    assert r1.dataset is d
    assert r1.name == "my name"

    assert r2.dataset is d
    assert r2.name == "my name also"
    assert r2.url == "http://foo"
    assert r2.foo == "bar"


def test_dataset_extras(testcli):
    c = testcli

    d = c.datasets.create(name="test_dataset_add_resources")
    d.add_resource(name="my name")

    assert d.extras == {}

    d.msg1 = "This is a message"
    assert d.extras == {"msg1": "This is a message"}

    d.proxy_invalidate()

    assert d.msg1 == "This is a message"
    del d.msg1
    assert not hasattr(d, "msg1")


def test_resource_extras(testcli):
    c = testcli
    d = c.datasets.create(name="test_dataset_add_resources")
    r = d.add_resource(name="my name")

    jcs = [
        {"a": 10, "b": ["hello", "world"]},
        "foobar",
        "",
        3.14,
        ["hello", {"type": "good"}, "world"],
    ]

    for v in jcs:
        r.foo = v
        r.proxy_invalidate
        assert r.foo == v
