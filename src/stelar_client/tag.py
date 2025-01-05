from uuid import UUID
from typing import List, Dict
from IPython.core.display import HTML
from IPython.display import display
from .proxy import (Id, NameId, RefList, StrField, Reference,
                    TagNameField)
from .apicall import GenericProxy
from .utils import client_for


class Vocabulary(GenericProxy):

    id = Id()
    name = NameId()
    tags = RefList('Tag')

    def add_tags(self, taglist):
        client_for(self).registry_for(Tag)
        for tagname in taglist:
            pass

class Tag(GenericProxy):
    id = Id()
    name = NameId(validator=TagNameField)
    vocabulary = Reference(Vocabulary, nullable=True, entity_name='vocabulary_id')

