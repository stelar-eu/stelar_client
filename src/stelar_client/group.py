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
    NameField,
    NameId,
    Property,
    RefList,
    StateField,
    StrField,
    derived_property,
)
from .resource import Resource


class Group(GenericProxy, ExtrasProxy):
    """
    Proxy for a STELAR Data Catalog group
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

    # users
    # groups
    # datasets
