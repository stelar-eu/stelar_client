from __future__ import annotations
import re
from uuid import UUID
from typing import List, Dict
from IPython.core.display import HTML
from IPython.display import display
from .proxy import (Id, NameId, RefList, StrField, Reference, Property,
                    TagNameField, derived_property)
from .apicall import GenericProxy, api_call, GenericCursor
from .utils import client_for


class Vocabulary(GenericProxy):

    id = Id()
    name = NameId()
    tags = RefList('Tag')

    @property
    def tagnames(self) -> list[str]:
        """The list of tag names."""
        ac = api_call(self)
        return ac.tag_list(vocabulary_id = str(self.id))

    @derived_property
    def tag_map(self, entity):
        return {
            t['name']: t
            for t in entity['tags']
        }

    def __getitem__(self, tagname: str) -> Tag:
        return self.tag_map[tagname]

    def add_tags(self, taglist: list[str]):
        """Add tags to this vocabulary

        Args:
           taglist (list[str]): the list of tags to add.
        """
        r = client_for(self).registry_for(Tag)
        for tagname in taglist:
            Tag.new(r, name=tagname, vocabulary=self)


class Tag(GenericProxy):
    id = Id()
    name = NameId(validator=TagNameField)
    vocabulary = Reference(Vocabulary, nullable=False, entity_name='vocabulary_id', trigger_sync=True)


class VocabularyCursor(GenericCursor):

    def __init__(self, client):
        super().__init__(client, Vocabulary)

    def fetch_list(self, *, limit: int, offset: int) -> list[str]:
        return [v.name for v in self.fetch(limit=limit, offset=offset)]

    def fetch(self, *, limit: int, offset: int) -> Iterator[Vocabulary]:
        registry = self.client.registry_for(Vocabulary)
        ac = api_call(self.client)
        result = ac.vocabulary_list()

        for entity in result:
            yield registry.fetch_proxy_for_entity(entity)



def tag_split(tagspec: str) -> Tuple[str|None, str]:
    m = re.fullmatch(r'((.{2,})\:)?([a-z0-9_-]{2,})', tagspec)
    if m is None:
        raise ValueError("Invalid tag specification")
    return m.groups()[1:]


class TagEncoding:
    """This is a component to be included as part of Client. It is responsible
    for translating tag lists quickly and correctly.

    To do this, it maintains two dictionaries which map vocabulary names to
    ids and conversely. This map is refreshed
    """
    def __init__(self, *args, **kwargs):
        self.client = client
        self.dirty = True
        self.voc_name_map = {}
        self.voc_id_map = {}

    def refresh_tag_vocabularies(self):
        ac = api_call(self)
        self.voc_name_map.clear()
        self.voc_id_map.clear()
        for voc in ac.vocabulary_list():
            self.voc_name_map[voc['id']] = voc['name']
            self.voc_id_map[voc['name']] = voc['id']
        self.dirty = False

    def taglist_to_entity(self, tags: list[str]) -> list[dict]:
        if self.dirty:
            self.refresh_tag_vocabularies()

        raise NotImplementedError
        


class TagList(Property):
    def __init__(self, doc="The tag list", short=True, **kwargs):
        super().__init__(self, validator=TLField, updatable=True, optional=False, 
                            doc=doc, short=short, **kwargs)

    