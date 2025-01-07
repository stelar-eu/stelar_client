from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Dict, Iterator, List
from uuid import UUID

from IPython.core.display import HTML
from IPython.display import display

from .decl import tag_split, validate_tagspec
from .fieldvalidation import AnyField
from .property import Property
from .proxy import Proxy

if TYPE_CHECKING:
    from .registry import RegistryCatalog
    from .typing import TagDictList, TagSpecList


class VocabularyIndex:
    """This is a component to be included as part of a registry catalog.
    It is responsible for indexing the tag vocabularies of a STELAR API,
    translating vocabulary names to IDs and back. As vocabularies do not
    change often at all, this index should only be included once in the lifetime
    of a client.
    """

    def __init__(self, catalog: RegistryCatalog, *args, **kwargs):
        self.catalog = catalog
        self.dirty = True
        self.refresh_count = 0
        self._name_to_id = {}
        self._id_to_name = {}

    @property
    def name_to_id(self):
        if self.dirty:
            self.refresh_tag_vocabularies()
        return self._name_to_id

    @property
    def id_to_name(self):
        if self.dirty:
            self.refresh_tag_vocabularies()
        return self._id_to_name

    def refresh_tag_vocabularies(self):
        """The registry catalog"""
        self._id_to_name.clear()
        self._name_to_id.clear()

        for voc in self.catalog.fetch_active_vocabularies():
            vid = voc["id"]
            vname = voc["name"]
            self._id_to_name[vid] = vname
            self._name_to_id[vname] = vid
        self.dirty = False
        self.refresh_count += 1


class TagListField(AnyField):
    def __init__(self):
        super().__init__(self, nullable=False, default=())
        self.add_check(self.to_taglist, 5)

    def to_taglist(self, tagl):
        if isinstance(tagl, str):
            raise ValueError("An iterable of strings was expected, got a single string")
        taglist = tuple(tagl)
        if not all(isinstance(v, str) for v in taglist):
            raise ValueError(
                "Unexpected tagspec", [v for v in taglist if not isinstance(v, str)]
            )
        badts = [ts for ts in taglist if not validate_tagspec(ts)]
        if badts:
            raise ValueError("Tag list contains non-valid tagspec(s)", badts)
        return taglist, True

    def convert_to_entity(
        self, value: TagSpecList, *, vocindex: VocabularyIndex, **kwargs
    ) -> TagDictList:
        tdl = []
        for tagspec in value:
            voc, tag = tag_split(tagspec)
            vid = vocindex.name_to_id[voc] if voc is not None else None
            tagdict = {"name": tag, "vocabulary_id": vid}
            tdl.append(tagdict)
        return tdl

    def convert_to_proxy(
        self, value: TagDictList, *, vocindex: VocabularyIndex, **kwargs
    ) -> TagSpecList:
        tsl = []
        for tagdict in value:
            vid = tagdict["vocabulary_id"]
            tname = tagdict["name"]
            if vid is not None:
                vname = vocindex.id_to_name[vid]
                tsl.append(f"{vname}:{tname}")
            else:
                tsl.append(tname)
        return tuple(tsl)


class TagList(Property):
    def __init__(self, doc="The tag list", short=True, **kwargs):
        super().__init__(
            validator=TagListField,
            updatable=True,
            optional=False,
            doc=doc,
            short=short,
            **kwargs,
        )

    def convert_entity_to_proxy(self, proxy, entity, **kwargs):
        vocindex = proxy.proxy_registry.catalog.vocabulary_index
        return super().convert_entity_to_proxy(
            proxy, entity, vocindex=vocindex, **kwargs
        )

    def convert_proxy_to_entity(self, proxy, entity, **kwargs):
        vocindex = proxy.proxy_registry.catalog.vocabulary_index
        return super().convert_proxy_to_entity(
            proxy, entity, vocindex=vocindex, **kwargs
        )

    def convert_to_create(
        self, proxy_type, create_props, entity_props, *, catalog, **kwargs
    ):
        vocindex = catalog.vocabulary_index
        return super().convert_to_create(
            proxy_type, create_props, entity_props, vocindex=vocindex, **kwargs
        )


class TaggableProxy(Proxy, entity=False):
    """A virtual base class for all proxies to entities that are taggable."""

    pass
