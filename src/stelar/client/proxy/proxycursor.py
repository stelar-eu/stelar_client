from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, Type, TypeVar
from uuid import UUID

from .decl import ProxyState
from .proxy import Proxy
from .registry import Registry

if TYPE_CHECKING:
    from ..client import Client


ProxyClass = TypeVar("ProxyClass", bound=Proxy)


class ProxyCursor(Registry[ProxyClass]):
    """Proxy cursors provide access functions to the collection of all entities of
    a given type.

    The cursor is used to fetch entities in a lazy way, and to provide
    a way to iterate over the entities, check for the existence of an entity by name,
    etc.
    """

    MAX_FETCH = 1000

    def __init__(self, client: Client, proxy_type: Type[ProxyClass]):
        """Initialize the cursor with the client and the proxy type."""
        self.client = client
        super().__init__(client, proxy_type)

    def create(self, **updates) -> ProxyClass:
        """Create a new entity of this type."""
        raise NotImplementedError

    def fetch_list(self, *, limit, offset) -> list[str]:
        """Lists entities of this type."""
        raise NotImplementedError

    def fetch(self, *, limit, offset) -> Iterator[ProxyClass]:
        """Fetch entities of this type."""
        raise NotImplementedError

    def get(self, name_or_id, default=None) -> ProxyClass:
        """Get an entity by name or ID."""
        raise NotImplementedError

    def __getitem__(self, item: str | UUID | slice) -> ProxyClass | list[ProxyClass]:
        """Get an entity by name or ID, or get a list of entities.

        A cursor behaves in a limited way as a (read-only) list of entities.
        If C is a cursor, then
        - C[UUID] returns the entity with the given UUID
        - C[str] returns the entity with the given name
        - C[:] returns a list of 'all' entities (up to some limit)
        - C[5:10] returns a list of the entities from 5 to 10, in some standard order.
        """
        if isinstance(item, slice):
            offset = item.start if item.start is not None else 0
            if offset < 0:
                raise ValueError("Bad offset")
            if item.step is not None:
                limit = item.step
            elif item.stop is not None:
                limit = item.stop - offset
            else:
                limit = self.MAX_FETCH
            if limit < 0:
                raise ValueError("Bad limit")
            # CUT OFF
            if limit > self.MAX_FETCH:
                limit = self.MAX_FETCH

            return self.fetch_list(limit=limit, offset=offset)
            # return list(self.fetch(limit=limit, offset=offset))

        elif isinstance(item, (str, UUID)):
            proxy = self.get(item)
            if proxy is None:
                raise KeyError("Entity not found")
            return proxy
        else:
            raise TypeError(
                f"Cannot fetch {self.proxy_type.__name__} by {item}: string or UUID is expected"
            )

    def __contains__(self, item) -> bool:
        """Check if an entity exists.

        The item can be a string, a UUID, or a proxy object. If it is a proxy object,
        the check is done on the proxy state not being ERROR.

        If the item is a string or a UUID, the check is done by looking the entity up
        in the STELAR API. Note that, for Data Catalog entities, a string may designate
        either an ID or a name.
        """
        if isinstance(item, self.proxy_type):
            return item.proxy_state is not ProxyState.ERROR
        elif isinstance(item, (str, UUID)):
            return self.get(item) is not None
        else:
            return False
