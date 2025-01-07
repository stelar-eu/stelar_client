from typing import Dict, List
from uuid import UUID

from IPython.core.display import HTML
from IPython.display import display

from .apicall import GenericProxy, api_call
from .proxy import (
    BoolField,
    DateField,
    ExtrasProperty,
    ExtrasProxy,
    Id,
    NameId,
    Property,
    RefList,
    StateField,
    StrField,
    TaggableProxy,
    TagList,
    derived_property,
)
from .resource import Resource


class GroupBase(GenericProxy, ExtrasProxy, TaggableProxy, entity=False):
    """
    Proxy for a STELAR Data Catalog group and organization.
    This is an abstract class. The group subclass is
    defined later.
    """

    id = Id()
    name = NameId()
    type = Property(validator=StrField(nullable=False))

    state = Property(validator=StateField)
    created = Property(validator=DateField)

    approval_status = Property(validator=StrField(), updatable=True)

    title = Property(validator=StrField, updatable=True)
    description = Property(validator=StrField, updatable=True)
    image_url = Property(validator=StrField(), updatable=True)
    extras = ExtrasProperty()
    tags = TagList()

    # users
    # groups
    # datasets


class Group(GroupBase):
    pass


class Organization(GroupBase):
    pass
