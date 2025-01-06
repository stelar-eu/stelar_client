from uuid import UUID
from typing import List, Dict
from IPython.core.display import HTML
from IPython.display import display
from .resource import Resource
from .proxy import (Property, Id, NameId, RefList, DateField, StrField, StateField,
                    BoolField, NameField, ExtrasProperty, ExtrasProxy)
from .apicall import GenericProxy

class Organization(GenericProxy, ExtrasProxy):
    """
    Proxy for a STELAR Data Catalog organization
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

    users = RefList('User')
    groups = RefList('Group')

    # tags
    # packages
