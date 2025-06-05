from stelar.client import Rel


def test_rel_enum():
    """Test the Rel enum."""

    for rel in Rel:
        assert isinstance(rel, Rel)
        assert isinstance(rel.value, str)
        assert rel.name.lower() == rel.value

    for rel in Rel:
        assert rel.peer().peer() is rel
        assert rel.is_canonical() or rel.peer().is_canonical()


def test_relationship_create(testcli):
    c = testcli

    rels = c.GET("v2/relationships/iris").json()["result"]
    assert len(rels) > 0
