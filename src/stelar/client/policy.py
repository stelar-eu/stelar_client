from functools import cached_property

from .api_call import api_call
from .generic import GenericCursor, GenericProxy
from .proxy import BoolField, DateField, Id, Property, StrField


class Policy(GenericProxy):
    """
    A proxy for a STELAR policy.
    """

    id = Id(entity_name="policy_uuid")

    creator = Property(
        validator=StrField(nullable=False),
        entity_name="user_id",
        doc="The user who created the policy.",
    )

    active = Property(
        validator=BoolField(nullable=False, default=True),
        updatable=False,
        optional=False,
        doc="Whether the policy is active or not.",
    )

    created_at = Property(
        validator=DateField(nullable=False), updatable=False, optional=False
    )

    policy_name = Property(
        validator=StrField(nullable=False),
        entity_name="policy_familiar_name",
        updatable=True,
        optional=False,
        doc="The name of the policy to be applied.",
    )

    @cached_property
    def spec(self):
        """
        A property that returns the policy content as a byte array.
        """
        return api_call(self).policy_spec(str(self.proxy_id))


class PolicyCursor(GenericCursor):
    """
    A cursor for iterating over policies.
    """

    def __init__(self, client):
        super().__init__(client, Policy)

    def create(self, policy_yaml: bytes) -> Policy:
        """
        Create a new policy.

        Args:
            spec (bytes): The policy specification as a byte array.
            **kwargs: Additional keyword arguments for the policy.

        Returns:
            Policy: The created policy.
        """
        ac = api_call(self)
        result = ac.policy_create(policy_yaml=policy_yaml)
        return self.fetch_proxy_for_entity(result)

    @property
    def active(self):
        return self.get("active", None)
