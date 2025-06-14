from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional
from uuid import UUID

from .api_call import api_call
from .proxy import EntityNotFound
from .utils import client_for

if TYPE_CHECKING:
    from .client import Client
    from .package import PackageProxy

    MatchExpr = PackageProxy | UUID | str | type[PackageProxy] | None


class Rel(Enum):
    """Enum for relationship types."""

    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"
    DEPENDS_ON = "depends_on"
    DEPENDENCY_OF = "dependency_of"
    DERIVES_FROM = "derives_from"
    HAS_DERIVATION = "has_derivation"
    LINKS_TO = "links_to"
    LINKED_FROM = "linked_from"

    def is_canonical(self) -> bool:
        """Return True if the relationship is forward, False if it is backward."""
        return self in CANONICAL

    def peer(self) -> Rel:
        """Return the peer relationship type."""
        return PEER_MAP[self]


CANONICAL = [Rel.CHILD_OF, Rel.DEPENDS_ON, Rel.DERIVES_FROM, Rel.LINKS_TO]
PEERS = [
    (Rel.PARENT_OF, Rel.CHILD_OF),
    (Rel.DEPENDENCY_OF, Rel.DEPENDS_ON),
    (Rel.HAS_DERIVATION, Rel.DERIVES_FROM),
    (Rel.LINKS_TO, Rel.LINKED_FROM),
]
PEER_MAP = {rel1: rel2 for rel1, rel2 in PEERS} | {rel2: rel1 for rel1, rel2 in PEERS}


def entity_data_matches(edata: Dict[str, Any], match: MatchExpr) -> bool:
    """Check if the entity data matches the given match expression.

    A match expression can be:
    - A proxy object
    - A UUID
    - A string matching the name of the package entity
    - A proxy type (Dataset, Process, etc.) matching the type
    - None (to ignore that part of the match)

    Args:
        edata: The entity data to check against.
        match: The match expression to check.

    Returns:
        bool: True if the entity data matches the expression, False otherwise.
    """
    from .package import PackageProxy

    if match is None:
        return True
    elif isinstance(match, PackageProxy):
        return edata.get("id") == match.proxy_id
    elif isinstance(match, UUID):
        return edata.get("id") == match
    elif isinstance(match, str):
        return edata.get("name") == match
    elif isinstance(match, type):
        return edata.get("type") == match.__name__.lower()
    else:
        return False


class Relationship:
    @classmethod
    def from_triple(
        cls,
        subject: PackageProxy,
        rel: Rel,
        object: PackageProxy,
        comment: Optional[str] = None,
    ) -> Relationship:
        client = client_for(subject)
        rel = Rel(rel).value
        reldata = {
            "subject": str(subject.proxy_id),
            "subject_name": subject.name,
            "subject_type": subject.type,
            "object": str(object.proxy_id),
            "object_name": object.name,
            "object_type": object.type,
            "relationship": rel,
            "comment": comment,
        }
        return cls(client, reldata)

    def __init__(self, client: Client, reldata: Dict[str, Any]) -> None:
        self.client: Client = client
        self.subject_id: UUID = UUID(reldata["subject"])
        self.subject_name: str = reldata["subject_name"]
        self.subject_type: str = reldata["subject_type"]

        self.object_id: UUID = UUID(reldata["object"])
        self.object_name: str = reldata["object_name"]
        self.object_type: str = reldata["object_type"]

        self.relationship: Rel = Rel(reldata["relationship"])
        self.comment: Optional[str] = reldata.get("comment", None)

    @property
    def subject(self) -> PackageProxy:
        """Return a proxy to the subject of the relationship."""
        return self.client.registry_for_type(self.subject_type).fetch_proxy(
            self.subject_id
        )

    @property
    def object(self) -> PackageProxy:
        """Return a proxy to the object of the relationship."""
        return self.client.registry_for_type(self.object_type).fetch_proxy(
            self.object_id
        )

    def subject_data(self) -> Dict[str, Any]:
        """Return a dictionary with the subject's data."""
        return {
            "id": self.subject_id,
            "name": self.subject_name,
            "type": self.subject_type,
        }

    def object_data(self) -> Dict[str, Any]:
        """Return a dictionary with the object's data."""
        return {
            "id": self.object_id,
            "name": self.object_name,
            "type": self.object_type,
        }

    def __repr__(self) -> str:
        return f"<Relationship {self.subject_name} {self.relationship.value} {self.object_name}>"

    def __str__(self) -> str:
        return f"{self.subject_name} --{self.relationship.value}--> {self.object_name}"

    def __eq__(self, other: Relationship) -> bool:
        if not isinstance(other, Relationship):
            return False

        if self.relationship is other.relationship:
            return (
                self.subject_data() == other.subject_data()
                and self.object_data() == other.object_data()
            )
        elif self.relationship.peer() is other.relationship:
            return (
                self.subject_data() == other.object_data()
                and self.object_data() == other.subject_data()
            )
        else:
            return False

    def __hash__(self) -> int:
        """Return a hash of the relationship."""
        if self.relationship.is_canonical():
            return hash((self.subject_id, self.object_id, self.relationship))
        else:
            return hash((self.object_id, self.subject_id, self.relationship.peer()))

    def matches(
        self,
        subj: MatchExpr,
        rel: Rel | str | None,
        obj: MatchExpr,
    ) -> bool:
        """Check if the relationship matches the given subject, relationship type, and object.

        Matching is semantic, i.e., a PARENT_OF will match
        a CHILD_OF relationship if the subject and object are reversed.

        A match expression can be
        - A proxy object
        - A UUID
        - A string matching the name of the package entity
        - A proxy type (Dataset, Process, etc.) matching the type
        - None (to ignore that part of the match)

        Args:
            subj: The subject to match against, either a PackageProxy or UUID.
            rel: The relationship type to match against, if specified.
            obj: The object to match against, either a PackageProxy or UUID.

        Returns:
            bool: True if the relationship matches the given subject and optional relationship type,
                False otherwise.
        """

        return (
            (rel is None or self.relationship is Rel(rel))
            and entity_data_matches(self.subject_data(), subj)
            and entity_data_matches(self.object_data(), obj)
        ) or (
            (rel is None or self.relationship.peer() is Rel(rel))
            and entity_data_matches(self.subject_data(), obj)
            and entity_data_matches(self.object_data(), subj)
        )

    def peer(self) -> Relationship:
        """Return the peer relationship."""
        return Relationship(
            self.client,
            {
                "subject": str(self.object_id),
                "subject_name": self.object_name,
                "subject_type": self.object_type,
                "object": str(self.subject_id),
                "object_name": self.subject_name,
                "object_type": self.subject_type,
                "relationship": self.relationship.peer().value,
                "comment": self.comment,
            },
        )

    def canonical(self) -> Relationship:
        """Return the canonical version of the relationship."""
        if self.relationship.is_canonical():
            return self
        else:
            return self.peer()

    def to_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation of the relationship."""
        return {
            "subject": str(self.subject_id),
            "subject_name": self.subject_name,
            "subject_type": self.subject_type,
            "object": str(self.object_id),
            "object_name": self.object_name,
            "object_type": self.object_type,
            "relationship": self.relationship.value,
            "comment": self.comment,
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Update the relationship from a dictionary."""
        self.subject_id = UUID(data["subject"])
        self.subject_name = data["subject_name"]
        self.subject_type = data["subject_type"]
        self.object_id = UUID(data["object"])
        self.object_name = data["object_name"]
        self.object_type = data["object_type"]
        self.relationship = Rel(data["relationship"])
        self.comment = data.get("comment", None)

    def set_comment(self, new_comment: str) -> None:
        """Set a new comment for the relationship."""
        ac = api_call(self.client)
        r = ac.relationship_update(
            str(self.subject_id),
            self.relationship.value,
            str(self.object_id),
            comment=new_comment,
        )
        self.from_dict(r)

    def delete(self) -> None:
        """Delete the relationship."""
        ac = api_call(self.client)
        ac.relationship_delete(
            str(self.subject_id), self.relationship.value, str(self.object_id)
        )

    def exists(self) -> bool:
        """Check if the relationship exists in the database."""
        ac = api_call(self.client)
        try:
            ac.relationship_show(
                str(self.subject_id), self.relationship.value, str(self.object_id)
            )
            return True
        except EntityNotFound:
            return False

    def __bool__(self) -> bool:
        """Return True if the relationship exists, False otherwise."""
        return self.exists()


class Relationships(set):
    """A set of relationships."""

    @classmethod
    def from_api(
        cls, client: Client, reldata: Iterable[Dict[str, Any]]
    ) -> Relationships:
        """Create a Relationships from API data."""
        return cls(client, {Relationship(client, r) for r in reldata})

    def __init__(
        self, client: Client, relationships: Iterable[Relationship] = []
    ) -> None:
        super().__init__(relationships)
        self.client: Client = client

    def matching(
        self,
        subj: MatchExpr,
        rel: Optional[Rel | str],
        obj: MatchExpr,
    ) -> Relationships:
        """Return the relationships matching a pattern.

        This method filters the relationships in the set based on the provided
        subject, rel and object. If any of these parameters are None, they are
        ignored in the matching. Note that matching is done semantically,
        i.e., a PARENT_OF matches a CHILD_OF, reversing the subject and object.

        For this, the `matches` method of the `Relationship` class is used.

        Args:
            subj: The subject to match against, either a PackageProxy or UUID.
            rel: The relationship type to match against, if specified.
            obj: The object to match against, either a PackageProxy or UUID.

        Returns:
            Relationships: A new set of relationships that match the criteria.
        """
        return Relationships(
            self.client,
            {r for r in self if r.matches(subj, rel, obj)},
        )

    def objects(self, ptype: type[PackageProxy] | None = None) -> set[PackageProxy]:
        """Return a set of the objects in the relationships.

        This call is similar to `entities()`, but only returns the objects
        of the relationships, optionally filtered by type. Note that the

        Args:
            ptype: If specified, only return objects of this type.

        Returns:
            A set of the objects in the relationships.
        """
        entset = set()
        for r in self:
            obj = r.object
            if ptype is None or isinstance(obj, ptype):
                entset.add(obj)
        return entset

    def entities(self) -> set[PackageProxy]:
        """Return a set of entities in the relationships.

        Entities are either subjects or objects of some relationship.
        """
        entset = set()
        for r in self:
            entset.add(r.subject)
            entset.add(r.object)
        return entset

    def delete(self) -> None:
        """Delete all relationships in the set."""
        for r in self:
            r.delete()
        self.clear()

    def __or__(self, other: Relationships) -> Relationships:
        """Return the union of two Relationships sets."""
        return Relationships(self.client, self.union(other))

    def __and__(self, other: Relationships) -> Relationships:
        """Return the intersection of two Relationships sets."""
        return Relationships(self.client, self.intersection(other))

    def __sub__(self, other: Relationships) -> Relationships:
        """Return the difference of two Relationships sets."""
        return Relationships(self.client, self.difference(other))

    def __xor__(self, other: Relationships) -> Relationships:
        """Return the symmetric difference of two Relationships sets."""
        return Relationships(self.client, self.symmetric_difference(other))


class RelProxy:
    """A proxy for a set of relationships."""

    def __init__(self, subj: PackageProxy):
        self.subject = subj
        self.relationship = None

    def _to_api(self, rel: Rel | str, obj: PackageProxy | UUID) -> str:
        subj = str(self.subject.proxy_id)
        if isinstance(rel, Rel):
            rel = rel.value

        from .package import PackageProxy

        if isinstance(obj, PackageProxy):
            obj = str(obj.id)
        elif isinstance(obj, UUID):
            obj = str(obj)

        return subj, rel, obj

    def get(self, rel: Rel | str, obj: PackageProxy | UUID) -> Relationship:
        subj, rel, obj = self._to_api(rel, obj)
        ac = api_call(self.subject)
        reldata = ac.relationship_show(subj, rel, obj)
        return Relationship(ac.client, reldata)

    def __call__(self, rel: Rel | str | None = None) -> Relationships:
        """Get all relationships for the subject."""
        subj, rel, obj = self._to_api(rel, None)
        ac = api_call(self.subject)
        reldata = ac.relationships_fetch(str(self.subject.id), rel, obj)
        return Relationships.from_api(ac.client, reldata)

    def add(
        self, rel: Rel | str, obj: PackageProxy | UUID, comment: Optional[str] = None
    ) -> Relationship:
        """Add a relationship to the subject."""
        subj, rel, obj = self._to_api(rel, obj)
        ac = api_call(self.subject)
        reldata = ac.relationship_create(subj, rel, obj, comment)
        return Relationship(ac.client, reldata)

    def remove(self, rel: Rel | str, obj: PackageProxy | UUID) -> None:
        """Remove a relationship from the subject."""
        subj, rel, obj = self._to_api(rel, obj)
        ac = api_call(self.subject)
        ac.relationship_delete(subj, rel, obj)

    @property
    def subject_id(self) -> UUID:
        """Return the ID of the subject."""
        return self.subject.proxy_id

    @property
    def depends_on(self) -> Relationships:
        return self(Rel.DEPENDS_ON)

    @property
    def dependency_of(self) -> Relationships:
        return self(Rel.DEPENDENCY_OF)

    @property
    def parent_of(self) -> Relationships:
        return self(Rel.PARENT_OF)

    @property
    def child_of(self) -> Relationships:
        return self(Rel.CHILD_OF)

    @property
    def derives_from(self) -> Relationships:
        return self(Rel.DERIVES_FROM)

    @property
    def has_derivation(self) -> Relationships:
        return self(Rel.HAS_DERIVATION)

    @property
    def links_to(self) -> Relationships:
        return self(Rel.LINKS_TO)

    @property
    def linked_from(self) -> Relationships:
        return self(Rel.LINKED_FROM)
