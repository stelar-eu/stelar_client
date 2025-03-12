import pytest

from stelar.client import Dataset, Process, Tool, Workflow


@pytest.mark.parametrize(
    "proxy_type",
    [Dataset, Tool, Process, Workflow],
)
def test_search_for_type(testcli, proxy_type):
    pass
