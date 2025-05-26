from __future__ import annotations

from functools import cached_property
from typing import Iterator

from .generic import GenericCursor, GenericProxy, api_call
from .proxy import BoolField, DateField, Id, Property, StrField, derived_property


class User(GenericProxy):
    id = Id()

    username = Property(validator=StrField())

    fullname = Property(validator=StrField())
    first_name = Property(validator=StrField(), updatable=True)
    last_name = Property(validator=StrField(), updatable=True)

    email = Property(validator=StrField(), updatable=True)
    email_verified = Property(validator=BoolField(), updatable=True)

    @derived_property
    def roles(self, entity):
        return tuple(entity.get("roles", []))

    joined_date = Property(validator=DateField())
    active = Property(validator=BoolField(), updatable=True)


class UserCursor(GenericCursor[User]):
    def __init__(self, client):
        super().__init__(client, User)

    def create(self, **kwargs) -> User:
        """
        Create a new user.

        Args:
            **kwargs: The user attributes to set.

        Returns:
            User: The created user.
        """
        # The user_create method is needed to support providing
        # the password as a keyword argument.
        ac = api_call(self.client)
        result = ac.user_create(**kwargs)
        return self.fetch_proxy_for_entity(result)

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
