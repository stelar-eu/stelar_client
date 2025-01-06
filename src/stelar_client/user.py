from __future__ import annotations
from uuid import UUID
from typing import List, Dict, Iterator
from IPython.core.display import HTML
from IPython.display import display
from .resource import Resource
from .proxy import (Property, Id, NameId, RefList, DateField, StrField, StateField,
                    BoolField, NameField, ExtrasProxy, ExtrasProperty)
from .apicall import GenericProxy, GenericCursor, api_call


class User(GenericProxy):

    id = Id()
    name = NameId()

    password = Property(validator=StrField(nullable=False, minimum_len=8), updatable=True, optional=True)
    reset_key = Property(validator=StrField(nullable=False, minimum_len=8), updatable=True, optional=True)

    fullname = Property(validator=StrField(nullable=True), updatable=True)
    email = Property(validator=StrField(nullable=True), updatable=True)

    # The following keys are not being modeled in the client!!
    #
    # apikey
    # activity_streams_email_notifications
    # plugin_extras

    created = Property(validator=DateField)
    about = Property(validator=StrField)
    last_active = Property(validator=DateField)

    sysadmin = Property(validator=BoolField(nullable=False))
    state = Property(validator=StateField)
    image_url = Property(validator=StrField)


class UserCursor(GenericCursor):

    def __init__(self, client):
        super().__init__(client, User)

    def fetch_list(self, *, limit: int, offset: int) -> list[str]:
        registry = self.client.registry_for(User)
        ac = api_call(self.client)
        result = ac.user_list(all_fields = False)
        return result

    def fetch(self, *, limit: int, offset: int) -> Iterator[User]:
        registry = self.client.registry_for(User)
        ac = api_call(self.client)
        result = ac.user_list()

        for entity in result:
            yield registry.fetch_proxy_for_entity(entity)

