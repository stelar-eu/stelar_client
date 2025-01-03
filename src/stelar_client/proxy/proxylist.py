from __future__ import annotations
from typing import Optional, TYPE_CHECKING, TypeVar, Generic, Any, Iterator, Type
from uuid import UUID
from weakref import WeakValueDictionary
from .exceptions import InvalidationError
from .decl import ProxyState
from .proxy import Proxy

if TYPE_CHECKING:
    from ..client import Client
    from .property import RefList
    from .registry import Registry
    from .schema import Schema
    from .property import RefList


ProxyClass = TypeVar('ProxyClass', bound=Proxy)


class ProxyList(Generic[ProxyClass]):
    """
    Base class for "dynamic lists" of proxies. 
    
    The instances maintain lists of IDs and translate list operations 
    as if the list actually contained proxy objects.
    """

    def __init__(self, client: Client, proxy_type: Type[ProxyClass]):
        self.client = client
        self.proxy_type = proxy_type
        self.registry = client.registry_for(proxy_type)

    @property
    def coll(self) -> list[UUID]:
        raise NotImplementedError
    
    def resolve_proxy(self, item):
        """This is the main routine that transforms elements of
           the list to proxies.
        """
        return self.registry.fetch_proxy(item)

    def __iter__(self):
        for item in self.coll:
            yield self.resolve_proxy(item)
    
    def __len__(self):
        return len(self.coll)

    def __getitem__(self, item):
        if isinstance(item, slice):
            raise ValueError("Slices are not supported yet")
        return self.resolve_proxy(self.coll[item])
    
    def __repr__(self):
        return f"{self.proxy_type.__name__}{repr(self.coll)}"

    @property
    def ids(self):
        return list(self.coll)

    @property
    def df(self, *additional_fields, fields=None):
        """Generate a dataframe for the set of resources."""
        import pandas as pd
        def simplified(val):
            if isinstance(val, Proxy):
                if hasattr(val,'name'):
                    return val.name
                else:
                    return val.proxy_id
            else:
                return val

        if fields is None:
            fields = self.proxy_type.proxy_schema.short_list(set(additional_fields))
        data = {
            field: list() for field in fields
        }

        print("The collection=", self.coll)

        for proxy in self:
            for field in fields:
                data[field].append(simplified(getattr(proxy, field)))
        return pd.DataFrame(data=data)



class ProxySublist(ProxyList):
    """A proxy class that translates collection operations to operations
       on an entity sub-collection.
    """

    def __init__(self, property: RefList, owner: Proxy):
        super().__init__(owner.proxy_registry.catalog, property.proxy_type)
        self.property = property
        self.owner = owner

    def __delitem__(self, key):
        raise NotImplementedError(f"delitem  {self.property.owner.__name__}.{self.property.name}")

    def __iadd__(self, **kwargs):
        raise NotImplementedError(f"iadd {self.property.owner.__name__}.{self.property.name}")

    @property
    def coll(self):
        return self.property.get(self.owner)



class ProxyCursor(Generic[ProxyClass]):

    MAX_FETCH=1000

    def __init__(self, client: Client, proxy_type: Type[ProxyClass]):
        self.client = client
        self.proxy_type = proxy_type

    def create(self, **updates) -> ProxyClass:
        raise NotImplementedError
    
    def fetch_list(self, *, limit, offset) -> list[str]:
        """Lists entities of this type."""
        raise NotImplementedError

    def fetch(self, *, limit, offset) -> Iterator[ProxyClass]:
        raise NotImplementedError

    def get(self, name_or_id, default=None) -> ProxyClass:
        raise NotImplementedError

    def __getitem__(self, item: str|UUID|slice) -> ProxyClass|list[ProxyClass]:
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
            #return list(self.fetch(limit=limit, offset=offset))
        
        elif isinstance(item, (str,UUID)):
            proxy = self.get(item)
            if proxy is None:
                raise KeyError(f"Entity not found")
            return proxy
        else:
            raise TypeError(f"Cannot fetch {self.proxy_type.__name__} by {item}: string or UUID is expected")
        
    def __contains__(self, item) -> bool:
        if isinstance(item, self.proxy_type):
            return item.proxy_state is not ProxyState.ERROR
        elif isinstance(item, (str, UUID)):
            return self.get(item) is not None
        else:
            return False

