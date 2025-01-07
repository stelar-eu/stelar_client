from typing import TYPE_CHECKING, Dict, List
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
    Proxy,
    ProxyVec,
    RefList,
    StateField,
    StrField,
    TaggableProxy,
    TagList,
    derived_property,
)
from .resource import Resource

if TYPE_CHECKING:
    from .proxy import Proxy


class MemberList(ProxyVec):
    def __init__(self, client, proxy_type, members, capacities):
        super().__init__(client, proxy_type, members)
        self.capacities = capacities

    def to_df(self, *additional, fields=None):
        df = super().to_df(*additional, fields=fields)
        return df.assign(capacity=self.capacities)


# We need to cater to CKAN
# N.B. this will eventually be updated
entity_to_ckan = {
    "Dataset": "package",
    "User": "user",
    "Group": "group",
}


def get_members(group, proxy_type, capacity):
    ac = api_call(group)

    ckan_type = entity_to_ckan[proxy_type.__name__]
    result = ac.member_list(id=str(group.id), object_type=ckan_type, capacity=capacity)
    ids = [UUID(entry[0]) for entry in result]
    cap = [entry[2] for entry in result]
    return MemberList(ac.client, proxy_type, ids, cap)


class GroupBase(GenericProxy, ExtrasProxy, TaggableProxy, entity=False):
    """
    Proxy for a STELAR Data Catalog group and organization.
    This is an abstract class. The group subclass is
    defined later.
    """

    id = Id()
    name = NameId()
    is_organization = Property(validator=BoolField)
    type = Property(validator=StrField(nullable=False))

    state = Property(validator=StateField)
    created = Property(validator=DateField)
    approval_status = Property(validator=StrField(), updatable=True)

    title = Property(validator=StrField, updatable=True)
    description = Property(validator=StrField, updatable=True)
    image_url = Property(validator=StrField(), updatable=True)
    extras = ExtrasProperty()
    tags = TagList()

    @property
    def users(self):
        from .user import User

        return get_members(self, User, capacity=None)

    @property
    def datasets(self):
        from .dataset import Dataset

        return get_members(self, Dataset, capacity=None)

    @property
    def groups(self):
        return get_members(self, Group, capacity=None)

    def add(self, member: Proxy, capacity: str = ""):
        try:
            objtype = entity_to_ckan[member.__class__.__name__]
        except KeyError:
            raise TypeError(f"Cannot add {type(member)} to a group")

        ac = api_call(self)
        ac.member_create(
            id=str(self.id),
            object=str(member.proxy_id),
            object_type=objtype,
            capacity=capacity,
        )

    def remove(self, member: Proxy):
        try:
            objtype = entity_to_ckan[member.__class__.__name__]
        except KeyError:
            raise TypeError(f"Cannot add {type(member)} to a group")

        ac = api_call(self)
        ac.member_delete(
            id=str(self.id),
            object=str(member.proxy_id),
            object_type=objtype,
        )


class Group(GroupBase):
    pass


class Organization(GroupBase):
    pass
