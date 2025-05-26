import pytest

from stelar.client import Client
from stelar.client.base import KLMSInfo

#
#  A fixture with a sample context file
#


@pytest.fixture(scope="session")
def config_file(tmp_path_factory):
    ctxfile = tmp_path_factory.mktemp("data") / ".stelar"
    ctx = """
; Test context
[default]
base_url= http://klms.example.org/
username= joe
password= joesecret

; Another test context
[biglake]
base_url= http://big.example.org/
username= joe
password= joesecret
"""
    with open(ctxfile, "w") as f:
        f.write(ctx)
    return ctxfile


def test_normalize_urls(mocker):
    mocker.patch(
        "stelar.client.Client.authenticate",
        return_value={
            "token": "token",
            "refresh_token": "refresh",
            "expires_in": 100,
            "refresh_expires_in": 100,
        },
    )
    mocker.patch(
        "stelar.client.base.BaseAPI._get_api_info",
        return_value=KLMSInfo({"s3_api": "http://foo.bar.com"}),
    )

    cli = Client(base_url="http://user:pass@foo.bar.com")
    assert cli._base_url == "http://foo.bar.com/stelar"
    assert cli._api_url == "http://foo.bar.com/stelar/api/"

    cli = Client(base_url="https://user:pass@foo.bar.com/")
    assert cli._base_url == "https://foo.bar.com/stelar"
    assert cli._api_url == "https://foo.bar.com/stelar/api/"

    cli = Client(base_url="https://user:pass@foo.bar.com/stelar")
    assert cli._base_url == "https://foo.bar.com/stelar"
    assert cli._api_url == "https://foo.bar.com/stelar/api/"


def test_context_default(mocker, config_file):
    mocker.patch(
        "stelar.client.Client.authenticate",
        return_value={
            "token": "token",
            "refresh_token": "refresh",
            "expires_in": 100,
            "refresh_expires_in": 100,
        },
    )
    mocker.patch(
        "stelar.client.base.BaseAPI._get_api_info",
        return_value=KLMSInfo({"s3_api": "http://minio.example.org"}),
    )

    c = Client(config_file=config_file)
    assert c._context is "default"
    assert c._base_url == "http://klms.example.org/stelar"
    Client.authenticate.assert_called_once_with(
        "http://klms.example.org/stelar",
        username="joe",
        password="joesecret",
        tls_verify=True,
    )


def test_context_given(mocker, config_file):
    mocker.patch(
        "stelar.client.Client.authenticate",
        return_value={
            "token": "token",
            "refresh_token": "refresh",
            "expires_in": 100,
            "refresh_expires_in": 100,
        },
    )
    mocker.patch(
        "stelar.client.base.BaseAPI._get_api_info",
        return_value=KLMSInfo({"s3_api": "http://minio.example.org"}),
    )

    c = Client(context="default", config_file=config_file)

    assert c._context == "default"
    assert c._base_url == "http://klms.example.org/stelar"
    Client.authenticate.assert_called_once_with(
        "http://klms.example.org/stelar",
        username="joe",
        password="joesecret",
        tls_verify=True,
    )


def test_context_noverify(mocker, config_file):
    mocker.patch(
        "stelar.client.Client.authenticate",
        return_value={
            "token": "token",
            "refresh_token": "refresh",
            "expires_in": 100,
            "refresh_expires_in": 100,
        },
    )
    mocker.patch(
        "stelar.client.base.BaseAPI._get_api_info",
        return_value=KLMSInfo({"s3_api": "http://minio.example.org"}),
    )

    c = Client(context="default", config_file=config_file, tls_verify=False)

    assert c._context == "default"
    assert c._base_url == "http://klms.example.org/stelar"
    Client.authenticate.assert_called_once_with(
        "http://klms.example.org/stelar",
        username="joe",
        password="joesecret",
        tls_verify=False,
    )
    assert c._tls_verify is False


def test_user_pass_in_url(mocker):
    mocker.patch(
        "stelar.client.Client.authenticate",
        return_value={
            "token": "token",
            "refresh_token": "refresh",
            "expires_in": 100,
            "refresh_expires_in": 100,
        },
    )
    mocker.patch(
        "stelar.client.base.BaseAPI._get_api_info",
        return_value=KLMSInfo({"s3_api": "http://minio.example.org"}),
    )

    c = Client(base_url="https://joe:joesecret@foo.bar.com")

    assert c._base_url == "https://foo.bar.com/stelar"
    assert c._token == "token"
    assert c._refresh_token == "refresh"
    c.authenticate.assert_called_once_with(
        "https://foo.bar.com/stelar",
        username="joe",
        password="joesecret",
        tls_verify=True,
    )


def test_no_user_pass(mocker):
    mocker.patch(
        "stelar.client.Client.authenticate",
        return_value={
            "token": "token",
            "refresh_token": "refresh",
            "expires_in": 100,
            "refresh_expires_in": 100,
        },
    )
    mocker.patch(
        "stelar.client.base.BaseAPI._get_api_info",
        return_value=KLMSInfo({"s3_api": "http://minio.example.org"}),
    )

    c = Client(base_url="https://foo.bar.com")

    assert c._base_url == "https://foo.bar.com/stelar"
    assert c._token == "token"
    assert c._refresh_token == "refresh"
    c.authenticate.assert_called_once_with(
        "https://foo.bar.com/stelar", username="", password="", tls_verify=True
    )


def test_user_pass_given(mocker):
    mocker.patch(
        "stelar.client.Client.authenticate",
        return_value={
            "token": "token",
            "refresh_token": "refresh",
            "expires_in": 100,
            "refresh_expires_in": 100,
        },
    )
    mocker.patch(
        "stelar.client.base.BaseAPI._get_api_info",
        return_value=KLMSInfo({"s3_api": "http://minio.example.org"}),
    )

    c = Client(base_url="https://foo.bar.com", username="joe", password="joesecret")

    assert c._base_url == "https://foo.bar.com/stelar"
    assert c._token == "token"
    assert c._refresh_token == "refresh"
    c.authenticate.assert_called_once_with(
        "https://foo.bar.com/stelar",
        username="joe",
        password="joesecret",
        tls_verify=True,
    )


@pytest.mark.skip
def test_fetch(testcli):
    dsets = testcli.catalog.get_datasets()
    assert len(dsets) > 0
    dset = dsets[0]
    print(dset.id)
    print(dset.name)
    print(dset.title)
    print(dset.notes)
