from __future__ import annotations

from .package import PackageCursor, PackageProxy
from .proxy import Property, StrField
from .proxy.fieldvalidation import EnumeratedField
from .proxy.property import DictProperty
from .task_spec import TaskSpec


class Workflow(PackageProxy):
    title = Property(validator=StrField, updatable=True)
    version = Property(
        validator=StrField(nullable=True, maximum_len=100), updatable=True
    )

    repository = Property(validator=StrField(nullable=True), updatable=True)
    executor = Property(validator=StrField(nullable=True), updatable=True)
    # resources = RefList(Resource, trigger_sync=True)


class ToolCategoryField(EnumeratedField):
    VALUES = [
        "discovery",
        "interlinking",
        "annotation",
        "other",
    ]


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

    # images = RefList("Image", trigger_sync=False)

    def task_spec(self, image=None):
        """Return a new TaskSpec initialized for this tool"""
        return TaskSpec(tool=self, image=image)


class ToolCursor(PackageCursor[Tool]):
    def __init__(self, client):
        super().__init__(client, Tool)
