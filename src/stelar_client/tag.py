from uuid import UUID
from typing import List, Dict
from IPython.core.display import HTML
from IPython.display import display
from .resource import Resource
from .proxy import (Id, NameId, RefList, DateField, StrField, Reference,
                    BoolField, NameField, ExtrasProxy, ExtrasProperty)
from .apicall import GenericProxy


class Vocabulary(GenericProxy):

    id = Id()
    name = NameId()
    tags = RefList('Tag')


class Tag(GenericProxy):
    id = Id()
    name = NameId()
    vocabulary = Reference(Vocabulary, nullable=True, entity_name='vocabulary_id')

