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

    def add_role(self, role: str):
        """
        Add a role to the user.

        Args:
            role (str): The role to add.
        """
        ac = api_call(self)
        entity = ac.user_add_role(str(self.proxy_id), role)
        self.proxy_sync(entity)

    def remove_role(self, role: str):
        """
        Remove a role from the user.

        Args:
            role (str): The role to remove.
        """
        ac = api_call(self)
        entity = ac.user_remove_role(str(self.proxy_id), role)
        self.proxy_sync(entity)

    def append_roles(self, roles: list[str]):
        """
        Append multiple roles to the user.

        Args:
            roles (list[str]): The roles to append.
        """
        ac = api_call(self)
        entity = ac.user_add_roles(str(self.proxy_id), roles)
        self.proxy_sync(entity)

    def set_roles(self, roles: list[str]):
        """
        Set the user's roles to a new list.

        Args:
            roles (list[str]): The new list of roles.
        """
        ac = api_call(self)
        entity = ac.user_set_roles(str(self.proxy_id), roles)
        self.proxy_sync(entity)


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

    def roles(self) -> list[str]:
        """
        Fetch the list of roles available in the system.

        Returns:
            list[str]: A list of role names.
        """
        ac = api_call(self.client)
        return [role["name"] for role in ac.roles_fetch()]
