import builtins
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


class MemberList(ProxyVec):
    def __init__(self, client, proxy_type, members, capacities):
        super().__init__(client, proxy_type, members)
        self.capacities = capacities

    def to_df(self, *additional, fields=None):
        df = super().to_df(*additional, fields=fields)
        return df.assign(capacity=self.capacities)


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

    def get_members(self, proxy_type: builtins.type[Proxy], capacity: str) -> MemberList:  # type: ignore
        """Get the members of the group.

        Args:
            proxy_type: The type of the members.
            capacity: The capacity of the members.
        Returns:
            MemberList, a list of members.
        """

        ac = api_call(self)

        list_members = ac.get_call(self.__class__, "list_members", proxy_type)

        result = list_members(id=str(self.id), capacity=capacity)
        ids = [UUID(entry[0]) for entry in result]
        cap = [entry[2] for entry in result]
        return MemberList(ac.client, proxy_type, ids, cap)

    @property
    def users(self):
        """Get the users of the group."""
        from .user import User

        return self.get_members(User, capacity=None)

    @property
    def datasets(self):
        """Get the datasets of the group."""
        from .dataset import Dataset

        return self.get_members(Dataset, capacity=None)

    @property
    def groups(self):
        """Get the groups of the group."""
        return self.get_members(Group, capacity=None)

    def add(self, member: Proxy, capacity: str = ""):
        """Add a member to the group.

        Args:
            member: The member to add.
            capacity: The capacity of the member.
        """
        ac = api_call(self)
        add_member = ac.get_call(self.__class__, "add", member.__class__)
        add_member(str(self.id), str(member.proxy_id), capacity=capacity)

    def remove(self, member: Proxy):
        """Remove a member from the group.

        Args:
            member: The member to remove.
        """
        ac = api_call(self)
        member_delete = ac.get_call(self.__class__, "remove", member.__class__)
        member_delete(str(self.id), str(member.proxy_id))


class Group(GroupBase):
    pass


class Organization(GroupBase):
    pass
