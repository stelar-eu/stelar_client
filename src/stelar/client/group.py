from typing import TYPE_CHECKING
from uuid import UUID

from .generic import GenericProxy, api_call
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
    StateField,
    StrField,
)

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

    list_members = ac.get_call(group.__class__, "list_members", proxy_type)

    result = list_members(id=str(group.id), capacity=capacity)
    ids = [UUID(entry[0]) for entry in result]
    cap = [entry[2] for entry in result]
    return MemberList(ac.client, proxy_type, ids, cap)


class GroupBase(GenericProxy, ExtrasProxy, entity=False):
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
        ac = api_call(self)
        add_member = ac.get_call(self.__class__, "add", member.__class__)
        add_member(str(self.id), str(member.proxy_id), capacity=capacity)

    def remove(self, member: Proxy):
        ac = api_call(self)
        member_delete = ac.get_call(self.__class__, "remove", member.__class__)
        member_delete(str(self.id), str(member.proxy_id))


class Group(GroupBase):
    pass


class Organization(GroupBase):
    pass
