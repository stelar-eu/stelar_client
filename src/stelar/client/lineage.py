from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from .client import Client
    from .proxy import Proxy
    from .resource import Resource


@dataclass
class ENode:
    id: UUID
    type: str
    lineage: "Lineage"
    incoming: list[ENode] = field(default_factory=list, init=False)
    outgoing: list[ENode] = field(default_factory=list, init=False)
    _ = KW_ONLY

    @property
    def ent(self) -> Proxy:
        """Return the proxy for this ENode."""
        return self.lineage.client.registry_for(self.type).fetch_proxy(self.id)


@dataclass
class EResource(ENode):
    def __post_init__(self):
        self.type = "Resource"

    _ = KW_ONLY
    package_id: UUID | None = None
    url: str | None = None
    label: str = ""


@dataclass
class ETask(ENode):
    def __post_init__(self):
        self.type = "Task"

    _ = KW_ONLY
    label: str = ""
    state: str = "unknown"
    image: str | None = None
    process_id: UUID | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class Lineage:
    """
    Represents a lineage graph between resources and tasks in the Stelar system.

    A lineage is a collection of tasks and resources that share a common ancestry
    or descendant.
    """

    def __init__(
        self, client: Client, focus_id: UUID, data: dict, forward: bool = False
    ):
        self.client = client
        self.focus_id = focus_id
        self.data = data
        self.forward = forward

        self.nodes: list[ENode] = []
        self.node: dict[UUID, ENode] = {}
        self.focus_node = None
        for node in self.data["nodes"]:
            if node["type"] == "Resource":
                enode = EResource(
                    id=UUID(node["id"]),
                    type=node["type"],
                    lineage=self,
                    label=node.get("label", ""),
                )
            elif node["type"] == "Task":
                enode = ETask(
                    id=UUID(node["id"]),
                    type=node["type"],
                    lineage=self,
                    label=node.get("label"),
                    state=node["state"],
                    image=node["image"],
                    start_date=datetime.fromisoformat(node["start_date"]),
                    end_date=datetime.fromisoformat(node["end_date"]),
                )
            else:
                raise ValueError(f"Unknown node type: {node['type']}")

            self.nodes.append(enode)
            self.node[enode.id] = enode
            if node.get("final"):
                self.focus_node = enode

        for s, t in self.data["edges"]:
            source = self.node[UUID(s)]
            target = self.node[UUID(t)]
            source.outgoing.append(target)
            target.incoming.append(source)

        self.resources: list[EResource] = [
            n for n in self.nodes if isinstance(n, EResource)
        ]
        self.tasks: list[ETask] = [n for n in self.nodes if isinstance(n, ETask)]

    @property
    def focus(self) -> Resource:
        """
        Return the focus resource of this lineage.

        The focus is the resource that is at the center of the lineage graph.
        """
        return self.client.resources.get(self.focus_id)

    def __repr__(self):
        return f"Lineage(focus={self.focus_id},forward={self.forward})"
