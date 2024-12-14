"""
    Dummy conftest.py for stelar_client.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    - https://docs.pytest.org/en/stable/fixture.html
    - https://docs.pytest.org/en/stable/writing_plugins.html
"""

import json, pathlib
import pytest
from stelar_client import Client


@pytest.fixture()
def testcli() -> Client:
    with open(pathlib.Path.home()/".stelar") as cred_file:
        cred = json.load(cred_file)

    ctx = cred['apitest']
    cli = Client(ctx["url"], username=ctx["username"], password=ctx["password"])
    yield cli

    # No logout yet. Once it is implemented,
    # here a logout must be posted.