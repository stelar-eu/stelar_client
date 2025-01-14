from uuid import *

import pytest
from proxy_utils import ProxyTestObj, TPCatalog

from stelar_client import *
from stelar_client.proxy.tag import TaggableProxy, TagList, TagListField
from stelar_client.vocab import *


@pytest.mark.parametrize(
    "tagspec, tagpair",
    [
        ("foo:bar", ("foo", "bar")),
        ("gg:aa:bar", ("gg:aa", "bar")),
        ("", None),
        ("a", None),
        ("a ", None),
        ("--", (None, "--")),
        ("s" * 101, None),
        (":::::::__", ("::::::", "__")),
    ],
)
def test_tag_split(tagspec, tagpair):
    if tagpair is None:
        with pytest.raises(ValueError):
            tag_split(tagspec)
    else:
        assert tag_split(tagspec) == tagpair


@pytest.mark.parametrize(
    "taglist",
    [[], {}, (), {"aa", "bbb:as"}, ["foo", "bar", "abasw"], dict(tag1="aa", tag2=44)],
)
def test_taglist_field(taglist):
    v = TagListField()
    v.validate(taglist)


@pytest.mark.parametrize("taglist", [["a"], "asdasda", 4, [["aa"]]])
def test_taglist_field_novalidate(taglist):
    v = TagListField()
    with pytest.raises(ValueError):
        v.validate(taglist)


def test_vocabulary_index():
    c = TPCatalog()

    did = str(uuid4())
    c.vocabs = [{"name": "daltons", "id": did}]

    assert c.vocabulary_index.dirty
    assert c.vocabulary_index.refresh_count == 0

    c.vocabulary_index.name_to_id["daltons"] == did
    c.vocabulary_index.id_to_name[did] == "daltons"
    assert not c.vocabulary_index.dirty
    assert c.vocabulary_index.refresh_count == 1


def test_taggable():
    class Foo(TaggableProxy, ProxyTestObj):
        tags = TagList()

    c = TPCatalog()
    c.vocabs = [{"name": "daltons", "id": uuid4()}]

    x = Foo.new(c)
    assert x.tags == ()

    x.tags = ("foo", "bar", "daltons:averell")
    assert "foo" in x.tags
    assert "bar" in x.tags
    assert "daltons:averell" in x.tags

    assert Foo.data[x.id]["tags"] == [
        {"name": "foo", "vocabulary_id": None},
        {"name": "bar", "vocabulary_id": None},
        {
            "name": "averell",
            "vocabulary_id": c.vocabulary_index.name_to_id["daltons"],
        },
    ]

    # assign by several types of sequences
    x.tags = []
    assert not x.tags

    x.tags = ["foo", "daltons:averell", "bar"]
    assert x.tags == ("foo", "daltons:averell", "bar")

    with pytest.raises(ConversionError) as e:
        x.tags = ["doltons:joe"]
    assert e.value.args[1] == "tags"

    x.proxy_reset()
    assert x.tags == ("foo", "daltons:averell", "bar")
