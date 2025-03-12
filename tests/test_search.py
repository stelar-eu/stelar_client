import jmespath
import pytest

from stelar.client import Dataset, Process, Tool, Workflow


@pytest.mark.parametrize(
    "proxy_type",
    [Dataset, Tool, Process, Workflow],
)
def test_search_for_type(testcli, proxy_type):
    cursor = testcli.cursor_for(proxy_type)

    # Create a query that counts all entities.
    query = cursor.search()

    ecount = query["count"]
    assert ecount > 0
    assert len(query["results"]) <= ecount
    assert all(e["type"] == proxy_type.__name__.lower() for e in query["results"])

    # Create queries that sort by name ascending and descending, and compare
    names_asc = jmespath.search(
        "results[*].name", cursor.search(sort="name asc", fl=["name"], limit=ecount)
    )
    names_desc = jmespath.search(
        "results[*].name", cursor.search(sort="name desc", fl=["name"], limit=ecount)
    )
    assert names_asc == list(reversed(names_desc))


def test_search_spatial(testcli):
    c = testcli
    try:
        c.datasets["test_dataset"].delete(purge=True)
    except Exception:
        pass

    d = c.datasets.create(name="test_dataset", title="A test")

    # Check that we do not have a spatial field.
    assert d.spatial is None

    # Check that we do not retrieve the dataset in a spatial query.
    fetched_names = jmespath.search(
        "results[*].name", c.datasets.search(bbox=[-180, -90, 180, 90], fl=["name"])
    )
    assert d.name not in fetched_names
