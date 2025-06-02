from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .package import PackageCursor, PackageProxy
from .proxy import Property, StrField, derived_property
from .proxy.fieldvalidation import EnumeratedField
from .proxy.property import DictProperty
from .task_spec import TaskSpec


class ToolCategoryField(EnumeratedField):
    VALUES = [
        "discovery",
        "interlinking",
        "annotation",
        "other",
    ]


#    {'is_manifest_list': False,                                            │(stelar) vsam@metallurgix:~/git/stelar/stelar_client$ git commit -a
#    'last_modified': 'Sun, 01 Jun 2025 19:45:45 -0000',                             │[main e7923b9] Fixed the proxy resync code related to task creation and termination.
#    'manifest_digest': 'sha256:6e4a55d6531c1aa8844164b552ba7b5f5ef9b30c5d9d94a145777│ 4 files changed, 49 insertions(+), 4 deletions(-)
# c7d26b7c572',                                                                       │(stelar) vsam@metallurgix:~/git/stelar/stelar_client$
#    'name': '0.2.0',                                                                │(stelar) vsam@metallurgix:~/git/stelar/stelar_client$
#    'reversion': False,                                                             │(stelar) vsam@metallurgix:~/git/stelar/stelar_client$ git pull
#    'size': 56837148,                                                               │Already up to date.
#    'start_ts': 1748807145
# }


@dataclass
class Image:
    """A container image used by a tool.

    Images are just information objects, they are not proxies.
    """

    is_manifest_list: bool
    last_modified: datetime
    manifest_digest: str
    tool: Tool  # The tool this image belongs to
    name: str
    reversion: bool
    size: int
    start_ts: datetime

    def __post_init__(self):
        if isinstance(self.last_modified, str):
            self.last_modified = datetime.strptime(
                self.last_modified, "%a, %d %b %Y %H:%M:%S -0000"
            )
        if isinstance(self.start_ts, int):
            self.start_ts = datetime.fromtimestamp(self.start_ts)

    @property
    def id(self):
        """Return a unique identifier for this image."""
        return f"stelar/{self.tool.name}:{self.name}"

    def __repr__(self):
        return f"Image({self.tool.name}/{self.name})"


class Tool(PackageProxy):
    # weird ones
    # license_id = Property(validator=StrField(nullable=True), updatable=True)
    git_repository = Property(validator=StrField(nullable=True), updatable=True)
    programming_language = Property(validator=StrField(nullable=True), updatable=True)
    version = Property(
        validator=StrField(nullable=True, maximum_len=100), updatable=True
    )

    inputs = DictProperty(str, str, updatable=True)
    outputs = DictProperty(str, str, updatable=True)
    parameters = DictProperty(str, str, updatable=True)

    category = Property(validator=ToolCategoryField(nullable=True), updatable=True)

    repository = Property(validator=StrField(nullable=False), updatable=False)

    @derived_property
    def images(self, entity):
        """Return a list of images associated with this tool."""
        images = entity.get("images", [])
        return [Image(tool=self, **image) for image in images]

    def task_spec(self, image=None):
        """Return a new TaskSpec initialized for this tool"""
        return TaskSpec(tool=self, image=image)


class ToolCursor(PackageCursor[Tool]):
    def __init__(self, client):
        super().__init__(client, Tool)
