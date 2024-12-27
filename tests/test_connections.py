import pytest
from pytest_mock import mocker
from stelar_client import Client


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
    mocker.patch("stelar_client.Client.authenticate", return_value=('token','refresh'))

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
    mocker.patch("stelar_client.Client.authenticate", return_value=('token','refresh'))
    c = Client(config_file=config_file)
    assert c._context is None
    assert c._base_url == "http://klms.example.org/stelar"
    Client.authenticate.assert_called_once_with("http://klms.example.org/stelar", 
                                                username="joe", password="joesecret", 
                                                tls_verify=True)


def test_context_given(mocker, config_file):
    mocker.patch("stelar_client.Client.authenticate", return_value=('token','refresh'))

    c = Client(context='default', config_file=config_file)

    assert c._context == 'default'
    assert c._base_url == "http://klms.example.org/stelar"
    Client.authenticate.assert_called_once_with("http://klms.example.org/stelar", 
                                                username="joe", password="joesecret", 
                                                tls_verify=True)

def test_context_noverify(mocker, config_file):
    mocker.patch("stelar_client.Client.authenticate", return_value=('token','refresh'))

    c = Client(context='default', config_file=config_file, tls_verify=False)

    assert c._context == 'default'
    assert c._base_url == "http://klms.example.org/stelar"
    Client.authenticate.assert_called_once_with("http://klms.example.org/stelar", 
                                                username="joe", password="joesecret", 
                                                tls_verify=False)
    assert c._tls_verify is False


def test_context_token():

    tok = "silly token"

    c = Client(base_url="https://klms.foo.com/", token= tok)
    assert c._base_url == "https://klms.foo.com/stelar"
    assert c._token == tok
    assert c._refresh_token is None

    c = Client(base_url="https://klms.foo.com/", token=tok, tls_verify=False)
    assert c._base_url == "https://klms.foo.com/stelar"
    assert c._token == tok
    assert c._refresh_token is None
    assert c._tls_verify is False
    
def test_context_token_nourl_raises():
    with pytest.raises(ValueError):
        c = Client(token="silly token")

def test_user_pass_in_url(mocker):
    mocker.patch("stelar_client.Client.authenticate", return_value=('token','refresh'))

    c = Client(base_url="https://joe:joesecret@foo.bar.com")

    assert c._base_url == "https://foo.bar.com/stelar"
    assert c._token == 'token'
    assert c._refresh_token == 'refresh'
    c.authenticate.assert_called_once_with("https://foo.bar.com/stelar",
                                           username="joe",
                                           password="joesecret", tls_verify=True)

def test_no_user_pass(mocker):
    mocker.patch("stelar_client.Client.authenticate", return_value=('token','refresh'))

    c = Client(base_url="https://foo.bar.com")

    assert c._base_url == "https://foo.bar.com/stelar"
    assert c._token == 'token'
    assert c._refresh_token == 'refresh'
    c.authenticate.assert_called_once_with("https://foo.bar.com/stelar",
                                           username="",
                                           password="", tls_verify=True)

def test_user_pass_given(mocker):
    mocker.patch("stelar_client.Client.authenticate", return_value=('token','refresh'))

    c = Client(base_url="https://foo.bar.com", username="joe", password="joesecret")

    assert c._base_url == "https://foo.bar.com/stelar"
    assert c._token == 'token'
    assert c._refresh_token == 'refresh'
    c.authenticate.assert_called_once_with("https://foo.bar.com/stelar",
                                           username="joe",
                                           password="joesecret", tls_verify=True)



@pytest.mark.skip
def test_fetch(testcli):
    dsets = testcli.catalog.get_datasets()
    assert len(dsets) > 0
    dset = dsets[0]
    print(dset.id)
    print(dset.name)
    print(dset.title)
    print(dset.notes)

