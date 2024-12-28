from uuid import UUID
from typing import List, Dict
from IPython.core.display import HTML
from IPython.display import display
from .resource import Resource
from .proxy import Proxy, Property, Id, RefList, DateField, StrField, BoolField
    

class Organization(Proxy):
    """
    Proxy for a STELAR Data Catalog organization
    """

    id = Id()
    name = Property()
    type = Property()

    state = Property(validator=StrField(nullable=False))
    created = Property(validator=DateField)

    approval_status = Property(validator=StrField(), updatable=True)

    title = Property(validator=StrField, updatable=True)
    description = Property(validator=StrField, updatable=True)
    image_url = Property(validator=StrField(), updatable=True)
    image_display_url = Property(validator=StrField(), updatable=True)

    # extras
    # tags
    # packages
    # users