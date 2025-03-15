from __future__ import annotations

from functools import cached_property
from typing import Iterator

from .generic import GenericCursor, GenericProxy, api_call
from .proxy import (
    BoolField,
    DateField,
    Id,
    NameId,
    Property,
    StateField,
    StrField,
    derived_property,
)


class User(GenericProxy):
    id = Id()

    username = Property(validator=StrField())

    fullname = Property(validator=StrField())
    first_name = Property(validator=StrField())
    last_name = Property(validator=StrField())

    email = Property(validator=StrField())

    @derived_property
    def roles(self, entity):
        return tuple(entity.get("roles", []))

    joined_date = Property(validator=DateField())
    active = Property(validator=BoolField())


class OldUser(GenericProxy):
    id = Id()
    name = NameId()

    password = Property(
        validator=StrField(nullable=False, minimum_len=8), updatable=True, optional=True
    )
    reset_key = Property(
        validator=StrField(nullable=False, minimum_len=8), updatable=True, optional=True
    )

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


class UserCursor(GenericCursor[User]):
    def __init__(self, client):
        super().__init__(client, User)

    @cached_property
    def current_user(self) -> User:
        """
        The current user of the client.

        Returns:
            dict: A dictionary containing the user's information.
        """
        return self.get(self.client._username)

    def fetch_list(self, *, limit: int, offset: int) -> list[str]:
        ac = api_call(self.client)
        result = ac.user_list(limit=limit, offset=offset)
        return result

    def fetch(self, *, limit: int, offset: int) -> Iterator[User]:
        registry = self.client.registry_for(User)
        ac = api_call(self.client)
        result = ac.user_fetch(limit=limit, offset=offset)

        for entity in result:
            yield registry.fetch_proxy_for_entity(entity)
