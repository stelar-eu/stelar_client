from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from .generic import GenericCursor, GenericProxy, api_call
from .proxy import (
    Id,
    NameId,
    ProxyList,
    Reference,
    RefList,
    Registry,
    RegistryCatalog,
    TagNameField,
    VocabNameField,
    derived_property,
)
from .utils import client_for, tag_split, validate_tagname

if TYPE_CHECKING:
    from .client import Client
    from .dataset import Dataset
    from .proxy.typing import TagSpecList


class Vocabulary(GenericProxy):
    """Vocabulary proxy provides manipulation of tag vocabularies."""

    id = Id()
    name = NameId(validator=VocabNameField)
    tags = RefList("Tag")

    @property
    def tagnames(self) -> list[str]:
        """The list of tag names."""
        return [t for t in self.tag_map]

    @property
    def tagspecs(self) -> TagSpecList:
        """The tagspecs of all tags in this vocabulary"""
        name = self.name
        return [f"{name}:{tagname}" for tagname in self.tagnames]

    @derived_property
    def tag_map(self, entity):
        """The tag_map is a dict mapping tag names to tag entities.

        This map is more conveniently accessed via the __getitem__ method
        on the vocabulary object.
        """
        return {t["name"]: t for t in entity["tags"]}

    def __getitem__(self, tagname: str) -> Tag:
        eid = UUID(self.tag_map[tagname]["id"])
        r = client_for(self).registry_for(Tag)
        return r.fetch_proxy(eid)

    def add_tags(self, taglist: list[str]):
        """Add tags to this vocabulary

        Args:
           taglist (list[str]): the list of tags to add.
        """
        r = client_for(self).registry_for(Tag)
        for tagname in taglist:
            Tag.new(r, name=tagname, vocabulary=self)

    # Overload to refresh cache
    def proxy_sync(self, entity=None):
        try:
            return super().proxy_sync(entity=entity)
        finally:
            self.proxy_registry.catalog.vocabulary_index.dirty = True

    @classmethod
    def new(
        cls,
        regspec: Registry | RegistryCatalog,
        *,
        name: str,
        tags: list[str] = [],
        autosync=True,
    ) -> Vocabulary:
        """Create a new vocabulary.

        Args:
            name (str): the name of the vocabulary.
            tags (list[str]): the list of tags to add to the vocabulary.
            autosync (bool): this is actually ignored.

        Returns:
            Vocabulary: the newly created vocabulary.
        """

        if not hasattr(cls, "proxy_schema"):
            raise TypeError(f"Class {cls.__name__} is not an entity class")

        tags = list(tags)
        if not all(validate_tagname(t) for t in tags):
            raise ValueError("Invalid tag name(s)", tags)

        newvoc = super().new(regspec, autosync=False, name=name, tags=[])

        ac = api_call(newvoc)
        ent = ac.vocabulary_create(name=name, tags=[{"name": t} for t in tags])

        newvoc.proxy_registry.register_proxy_for_entity(newvoc, ent)
        newvoc.proxy_from_entity(ent)
        newvoc.proxy_changed = None

        return newvoc


class Tag(GenericProxy):
    """A proxy for vocaublary tags.

    There is not much interesting functionality, since tags are not updatable.
    However, this proxy class allows for creation and deletion of vocabulary
    tags.

    Note that free tags (those without a vocabulary) in the Data Catalog are managed
    by the underlying CKAN implementation automatically (as they appear in tag fields
    for datasets, groups, organizations, etc.)
    """

    id = Id()
    name = NameId(validator=TagNameField)
    vocabulary = Reference(
        Vocabulary, nullable=False, entity_name="vocabulary_id", trigger_sync=True
    )

    @derived_property
    def tagspec(self, entity):
        tname = entity["name"]
        vid = entity["vocabulary_id"]
        if vid is not None:
            vname = self.proxy_registry.catalog.vocabulary_index.id_to_name[vid]
            return f"{vname}:{tname}"
        else:
            return tname

    def get_tagged_datasets(self) -> ProxyList[Dataset]:
        """Retrieve a number of datasets tagged with this tag.

        Note that there is an upper limit to the number of datasets
        (currently, 1000). For a more flexible access, the dataset search
        facility (Client.datasets.with_tag()) can be used.

        However, this call is convenient for 'rare' tags.
        """
        # Since tags are immutable, ignore own state
        c = client_for(self)
        return c.datasets.with_tag(self.tagspec)


class VocabularyCursor(GenericCursor[Vocabulary]):
    """Implement CKAN cursor functionalities for Vocabulary.

    N.B. Currently, this class is here as a placeholder and may eventually be
    removed.
    """

    def __init__(self, client):
        super().__init__(client, Vocabulary)


class TagCursor(GenericCursor[Tag]):
    """Tag cursors are a bit different, since they need to cater to
    free tags as well as vocabulary tags, and be fast about searching
    tags.

    The cursor fetches only retrieve free tags. However, there are other
    facilities that allow for the retrieval of all types of tags, as well
    as search operations using them.
    """

    def __init__(self, client: Client):
        super().__init__(client, Tag)

    def __getitem__(self, tagspec):
        if isinstance(tagspec, slice):
            return super().__getitem__(tagspec)

        ac = api_call(self)
        match tag_split(tagspec):
            case (None, tagname):
                entity = ac.tag_show(id=tagname)
            case (vocname, tagname):
                # Lookup the tag in the vocabulary index
                try:
                    self.client.vocabulary_index.dirty = True
                    entity = self.client.vocabulary_index.name_to_tags[vocname][tagname]
                except KeyError:
                    raise ValueError(f"Tag {tagspec} not found")
                # entity = ac.tag_show(id=tagname, vocabulary_id=vocname)
            case _:
                raise RuntimeError("Tag splitting, this is a bug")
        return self.client.registry_for(Tag).fetch_proxy_for_entity(entity)
