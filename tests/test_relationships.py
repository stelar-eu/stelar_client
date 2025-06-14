from uuid import uuid4

from stelar.client import Dataset, Process, Rel, Relationship, Relationships, Workflow


def test_rel_enum():
    """Test the Rel enum."""

    for rel in Rel:
        assert isinstance(rel, Rel)
        assert isinstance(rel.value, str)
        assert rel.name.lower() == rel.value

    for rel in Rel:
        assert rel.peer().peer() is rel
        assert rel.is_canonical() or rel.peer().is_canonical()


def test_relationship_class(testcli):
    c = testcli

    iris = c.datasets.get("iris")
    wine = c.datasets.get("wine")

    r = Relationship(
        c,
        {
            "subject": str(iris.id),
            "subject_name": iris.name,
            "subject_type": "dataset",
            "object": str(wine.id),
            "object_name": wine.name,
            "object_type": "dataset",
            "relationship": Rel.LINKS_TO.value,
            "comment": "This is a test relationship.",
        },
    )

    assert r.subject_id == iris.id
    assert r.object_id == wine.id
    assert r.subject_name == iris.name
    assert r.object_name == wine.name
    assert r.subject_type == "dataset"
    assert r.object_type == "dataset"
    assert r.relationship is Rel.LINKS_TO

    assert Relationship.from_triple(iris, Rel.LINKS_TO, wine) == r

    assert r.subject is iris
    assert r.object is wine

    assert r.subject_data() == {
        "id": iris.id,
        "name": iris.name,
        "type": "dataset",
    }
    assert r.object_data() == {
        "id": wine.id,
        "name": wine.name,
        "type": "dataset",
    }

    # Check the relationship exists in the database.
    assert r.exists()
    assert r  # Cast to boolean

    rpeer = r.peer()
    assert rpeer.subject_id == wine.id
    assert rpeer.object_id == iris.id
    assert rpeer.subject_name == wine.name
    assert rpeer.object_name == iris.name
    assert rpeer.subject_type == "dataset"
    assert rpeer.object_type == "dataset"
    assert rpeer.relationship is Rel.LINKED_FROM

    # Check the peer relationship exists in the database.
    assert rpeer.exists()

    assert r == rpeer
    assert rpeer.subject is wine
    assert rpeer.object is iris
    assert rpeer.canonical() == r
    assert rpeer.canonical().relationship is Rel.LINKS_TO


def test_relationship_not_exists(testcli):
    c = testcli

    iris = c.datasets.get("iris")
    wine = c.datasets.get("wine")

    r = Relationship.from_triple(iris, Rel.LINKS_TO, wine)
    assert r.exists()

    r.relationship = Rel.CHILD_OF
    assert not r.exists()

    r.subject_id = uuid4()
    r.name = "Nonexistent1"

    assert not r.exists()
    assert not r


def test_relationship_match(testcli):
    c = testcli

    iris = c.datasets.get("iris")
    wine = c.datasets.get("wine")
    proc = c.processes.get("simple_proc")

    r = Relationship.from_triple(iris, Rel.PARENT_OF, proc)

    assert r.matches(iris, Rel.PARENT_OF, proc)
    assert r.matches(iris, "parent_of", proc)
    assert r.matches(iris, None, proc)
    assert r.matches(iris, Rel.PARENT_OF, None)
    assert r.matches(iris, None, None)
    assert r.matches(None, Rel.PARENT_OF, Process)
    assert r.matches(Process, Rel.CHILD_OF, None)
    assert r.matches(None, None, None)

    # Check reverse relationship
    assert r.matches(proc, Rel.CHILD_OF, iris)
    assert r.matches(proc, "child_of", iris)
    assert r.matches(proc, None, iris)
    assert r.matches(proc, Rel.CHILD_OF, None)
    assert r.matches(proc, None, None)
    assert r.matches(None, Rel.CHILD_OF, Dataset)
    assert r.matches(Dataset, Rel.PARENT_OF, None)
    assert r.matches(None, Rel.PARENT_OF, None)
    assert r.matches(None, Rel.CHILD_OF, None)

    # Check non-matching cases
    assert not r.matches(iris, Rel.LINKS_TO, proc)
    assert not r.matches(iris, Rel.PARENT_OF, wine)
    assert not r.matches(wine, Rel.PARENT_OF, iris)
    assert not r.matches(Workflow, None, None)
    assert not r.matches(None, Rel.DEPENDENCY_OF, None)


def test_relationships(testcli):
    c = testcli

    # use test datasets
    dset1 = c.datasets.get("dataset1")
    dset2 = c.datasets.get("dataset2")
    dset3 = c.datasets.get("dataset3")
    proc = c.processes.get("simple_proc")

    # Create a relationship
    dset1.relationships.add(Rel.PARENT_OF, dset2, "Test relationship 1")
    dset1.relationships.add(Rel.PARENT_OF, dset3, "Test relationship 2")
    dset2.relationships.add(Rel.DEPENDS_ON, dset3, "Test relationship 3")
    dset3.add_relationship("depends_on", proc, "Test relationship 4")

    rs1 = dset1.relationships()
    rs2 = dset2.relationships()
    rs3 = dset3.relationships()
    rp = proc.relationships()

    assert len(rs1) == 2
    assert len(rs2) == 2
    assert len(rs3) == 3
    assert len(rp) == 1

    rall = rs1 | rs2 | rs3 | rp
    assert len(rall) == 4

    try:
        # check membership
        assert all(r in rall for r in rs1)
        assert all(r in rall for r in rs2)
        assert all(r in rall for r in rs3)
        assert all(r in rall for r in rp)

        # check relationships set operations
        assert rs1.objects() == {dset2, dset3}
        assert rs3.entities() == {dset1, dset2, dset3, proc}
        assert rs1.entities() == {dset1, dset2, dset3}
        assert rp.objects() == {dset3}
        assert rp.entities() == {dset3, proc}

        assert (rs1 ^ rs2 ^ rs3 ^ rp) == Relationships(c, {})
        assert rall - rs3 == rs1 & rs2

        assert set() <= rs3 <= rall
    finally:
        rall.delete()


def test_proxy_relationship_get(testcli):
    c = testcli

    iris = c.datasets.get("iris")
    wine = c.datasets.get("wine")

    # There should be a relationship iris --links_to--> wine.
    # Check with the API.
    checking = c.GET("v2/relationships/iris/links_to/wine").json()
    assert checking["success"]
    assert checking["result"]
    # Same as above
    assert Relationship.from_triple(iris, Rel.LINKS_TO, wine).exists()

    # Check with the relationship object.
    rel = iris.relationships.get("links_to", "wine")

    assert iris.relationships.get("links_to", "wine") == rel
    assert wine.relationships.get(Rel.LINKED_FROM, "iris") == rel

    assert rel == iris.relationships.get(Rel.LINKS_TO, wine)
    assert rel.subject_id == iris.id
    assert rel.object_id == wine.id
    assert rel.subject_name == iris.name
    assert rel.object_name == wine.name
    assert rel.subject_type == "dataset"
    assert rel.object_type == "dataset"
    assert rel.relationship == Rel.LINKS_TO
