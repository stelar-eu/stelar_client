import pytest


@pytest.fixture()
def vocab1(testcli):
    c = testcli
    vocab1 = c.vocabularies.create(name="vocab1", tags=["tag1", "tag2", "tag3"])
    yield vocab1
    vocab1.delete()


def test_vocabulary_create(testcli, vocab1):
    # c = testcli
    assert vocab1.name == "vocab1"
    assert vocab1.tagnames == ["tag1", "tag2", "tag3"]
    assert vocab1.tagspecs == ["vocab1:tag1", "vocab1:tag2", "vocab1:tag3"]


def test_vocabulary_list(testcli):
    c = testcli
    oldvoc = set(c.vocabularies[:])
    vocab1 = c.vocabularies.create(name="vocab1")
    vocab2 = c.vocabularies.create(name="vocab2")
    assert set(c.vocabularies[:]) == oldvoc | {vocab1, vocab2}
    vocab1.delete()
    vocab2.delete()
    assert set(c.vocabularies[:]) == oldvoc
