from __future__ import annotations
from uuid import UUID
from typing import List, Dict
from IPython.core.display import HTML
from IPython.display import display
from .proxy import (Id, NameId, RefList, StrField, Reference,
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


