"""
    Dummy conftest.py for stelar.client.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    - https://docs.pytest.org/en/stable/fixture.html
    - https://docs.pytest.org/en/stable/writing_plugins.html
"""


import pytest

from stelar.client import Client


@pytest.fixture(scope="session")
def testcontext() -> str:
    return "local"


def client_cleanup(cli):
    # Make sure that all datasets whose name
    # starts with "test_" are purged
    for m in cli.DC.package_autocomplete(q="test_", limit=1000)["result"]:
        if m["match_field"] == "name":
            cli.DC.dataset_purge(id=m["name"])


@pytest.fixture()
def testcli(testcontext) -> Client:
    cli = Client(testcontext)

    client_cleanup(cli)

    yield cli

    client_cleanup(cli)

    # No logout yet. Once it is implemented,
    # here a logout must be posted.
