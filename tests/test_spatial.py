import geojson as gj
import pytest

from stelar.client.proxy.decl import ProxyState
from stelar.client.spatial import GeoJSON


def test_geojson_field():
    f = GeoJSON(nullable=True)

    f.validate(None)
    f.validate(gj.utils.generate_random("Point"))
    f.validate(gj.utils.generate_random("Polygon"))
    f.validate(gj.utils.generate_random("LineString"))


@pytest.mark.parametrize(
    "value",
    [
        "foo",
        "Point",
        [3.2, 1.4],
        1.32,
        {"type": "Point"},
        {"type": "Point", "coordinates": [13]},
        {"type": "Point", "coordinates": []},
        {"type": "Polygon", "coordinates": [[1, 2], [3, 4], [5, 6], [1, 2]]},
        {"type": "Polygon", "coordinates": [[[1, 2], [3, 4], [5, 6], [2, 2]]]},
    ],
)
def test_geojson_field_invalid(value):
    f = GeoJSON(nullable=True)

    with pytest.raises(ValueError):
        f.validate(value)


def test_geojson_to_proxy():
    f = GeoJSON(nullable=True)

    assert f.convert_to_proxy(None) is None
    assert f.convert_to_proxy(gj.utils.generate_random("Point")).type == "Point"
    assert f.convert_to_proxy(gj.utils.generate_random("Polygon")).type == "Polygon"
    assert (
        f.convert_to_proxy(gj.utils.generate_random("LineString")).type == "LineString"
    )


def test_dataset_create_spatial(testcli):
    c = testcli

    try:
        c.DELETE("v2/datasets/test_dataset?purge=true")
    except Exception:
        pass

    d = c.datasets.create(name="test_dataset", title="A test")
    assert d.title == "A test"
    assert d.spatial is None
    assert c.api.dataset_show("test_dataset")["spatial"] is None

    with pytest.raises(ValueError):
        d.spatial = "foo"
    assert d.proxy_state is ProxyState.CLEAN
    with pytest.raises(ValueError):
        d.spatial = gj.Point()
    assert d.proxy_state is ProxyState.CLEAN

    poly = gj.utils.generate_random("Polygon")
    d.spatial = poly
    assert d.spatial == poly
    assert c.api.dataset_show("test_dataset")["spatial"] == poly

    d.delete(purge=True)
