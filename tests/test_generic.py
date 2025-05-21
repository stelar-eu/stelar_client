from stelar.client import Client, ProxyState


def test_standard_orgganization(testcli):
    org = testcli.organizations["stelar-klms"]
    assert org.name == "stelar-klms"


def test_create_org(testcli):
    for i in range(5):
        try:
            # Use the API to delete
            testcli.DC.organization_purge(id=f"test_org_{i}")
        except:
            pass

    norg = len(testcli.organizations[::])

    orgs = []
    for i in range(5):
        print(i)
        o = testcli.organizations.create(name=f"test_org_{i}")
        orgs.append(o)

    for i in range(5):
        assert testcli.organizations[f"test_org_{i}"] is orgs[i]

    for o in orgs:
        o.delete(purge=True)

    assert len(testcli.organizations[::]) == norg


def test_generic_proxy_create(testcontext):
    c = Client(testcontext)
    org = c.organizations["stelar-klms"]

    if "test_dataset" in c.datasets:
        c.datasets["test_dataset"].delete(purge=True)

    d = c.datasets.create(
        name="test_dataset",
        title="Test dataset",
        notes="A very simple dataset to test",
        maintainer="Alonso Church",
        url="https://stelar.tuc.gr/data",
    )

    assert d.name == "test_dataset"
    assert d.title == "Test dataset"
    assert d.notes == "A very simple dataset to test"
    assert d.maintainer == "Alonso Church"
    assert d.url == "https://stelar.tuc.gr/data"

    assert d.organization is c.organizations["stelar-klms"]
    assert len(d.resources) == 0

    d.delete(purge=True)
    assert d.proxy_state is ProxyState.ERROR
