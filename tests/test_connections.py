from stelar_client import Client


def test_urls():

    cli = Client("http://foo.bar.com")
    assert cli.base_url == "http://foo.bar.com/stelar/api"
    assert cli.api_url == "http://foo.bar.com/stelar/api"

    cli = Client("https://foo.bar.com/")
    assert cli.base_url == "https://foo.bar.com/stelar/api"
    assert cli.api_url == "https://foo.bar.com/stelar/api"

    cli = Client("https://foo.bar.com/stelar")
    assert cli.base_url == "https://foo.bar.com/stelar/api"
    assert cli.api_url == "https://foo.bar.com/stelar/api"
