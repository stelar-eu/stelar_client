from __future__ import annotations

from stelar.client.api_call import api_call
from stelar.client.package import PackageCursor
from stelar.client.proxy.fieldvalidation import EnumeratedField, UUIDField
from stelar.client.proxy.property import DictProperty, ListProperty

from .generic import GenericProxy
from .proxy import (
    DateField,
    ExtrasProperty,
    ExtrasProxy,
    Id,
    NameId,
    Property,
    Reference,
    RefList,
    StateField,
    StrField,
    TaggableProxy,
    TagList,
)
from .utils import client_for


class Workflow(GenericProxy, ExtrasProxy, TaggableProxy):
    id = Id()
    name = NameId()

    metadata_created = Property(validator=DateField)
    metadata_modified = Property(validator=DateField)
    state = Property(validator=StateField)
    type = Property(validator=StrField)
    creator = Property(validator=UUIDField, entity_name="creator_user_id")

    title = Property(validator=StrField, updatable=True)
    notes = Property(validator=StrField(nullable=True), updatable=True)
    author = Property(validator=StrField(nullable=True), updatable=True)
    author_email = Property(validator=StrField(nullable=True), updatable=True)
    maintainer = Property(validator=StrField(nullable=True), updatable=True)
    maintainer_email = Property(validator=StrField(nullable=True), updatable=True)

    # weird ones
    # license_id = Property(validator=StrField(nullable=True), updatable=True)
    repository = Property(validator=StrField(nullable=True), updatable=True)
    executor = Property(validator=StrField(nullable=True), updatable=True)
    version = Property(
        validator=StrField(nullable=True, maximum_len=100), updatable=True
    )

    # resources = RefList(Resource, trigger_sync=True)
    organization = Reference(
        "Organization",
        entity_name="owner_org",
        create_default="default_organization",
        updatable=True,
        trigger_sync=True,
    )

    groups = RefList("Group", trigger_sync=False)
    extras = ExtrasProperty()
    tags = TagList()


class Task(GenericProxy):
    id = Id(entity_name="task_exec_id")
    start_date = Property(validator=DateField)
    end_date = Property(validator=DateField(nullable=True))

    state = Property(validator=StrField)

    creator = Property(validator=StrField, entity_name="creator")
    process = Reference("Process", entity_name="workflow_exec_id", trigger_sync=False)

    messages = Property(validator=StrField, updatable=False, optional=True)
    metrics = DictProperty(str, str, updatable=False, optional=True)
    output = ListProperty(dict, updatable=False, optional=True)

    tool_name = Property(validator=StrField, optional=True)
    tool_image = Property(validator=StrField, optional=True)
    tags = DictProperty(str, str, updatable=False, optional=True)


class ExecStateField(EnumeratedField):
    VALUES = ["running", "succeeded", "failed"]


class Process(GenericProxy, ExtrasProxy, TaggableProxy):
    """Proxy object for workflow processes (executions)."""

    id = Id()
    name = NameId()

    start_date = Property(validator=DateField)
    end_date = Property(validator=DateField(nullable=True))
    workflow = Reference(
        "Workflow",
        updatable=True,
        nullable=True,
        entity_name="workflow",
        trigger_sync=False,
    )
    tasks = RefList("Task", trigger_sync=True)
    exec_state = Property(validator=StrField, updatable=True)

    metadata_created = Property(validator=DateField)
    metadata_modified = Property(validator=DateField)
    state = Property(validator=StateField)
    type = Property(validator=StrField)
    creator = Property(validator=StrField, entity_name="creator")
    # creator_id = Property(validator=StrField, entity_name="creator")

    start_date = Property(validator=DateField, updatable=False)
    end_date = Property(validator=DateField, updatable=True)
    exec_state = Property(validator=ExecStateField, updatable=False)

    title = Property(validator=StrField, updatable=True)
    notes = Property(validator=StrField(nullable=True), updatable=True)
    author = Property(validator=StrField(nullable=True), updatable=True)
    author_email = Property(validator=StrField(nullable=True), updatable=True)
    maintainer = Property(validator=StrField(nullable=True), updatable=True)
    maintainer_email = Property(validator=StrField(nullable=True), updatable=True)

    # weird ones
    url = Property(validator=StrField(nullable=True), updatable=True)
    version = Property(
        validator=StrField(nullable=True, maximum_len=100), updatable=True
    )

    # resources = RefList(Resource, trigger_sync=True)

    #
    # TODO
    #  tasks

    organization = Reference(
        "Organization",
        entity_name="owner_org",
        create_default="default_organization",
        updatable=True,
        trigger_sync=True,
    )

    groups = RefList("Group", trigger_sync=False)
    extras = ExtrasProperty()
    tags = TagList()

    def add_resource(self, **properties):
        """Add a new resource with the given properties.

        Example:  new_rsrc = d.add_resource(name="Profile", url="s3://datasets/a.json",
            format="json", mimetype="application/json")

        Args:
            **properties: The arguments to pass. See 'Resource' for details.
        """
        return client_for(self).resources.create(dataset=self, **properties)

    def terminate(self, new_state: str = "succeeded"):
        """Terminate the process execution.

        This call transitions the exec_state of the process to the given state.
        The only meaningful values are those validated with the ExecStateField
        (namely, 'running', 'succeeded', 'failed').

        Note, that the process must be 'running' for this call to have any effect.

        Args:
            new_state: The new state to transition to.
        """
        # Since the exec_state is not updatable, we need to use the API directly
        entity = api_call(self).process_patch(
            id=str(self.proxy_id), exec_state="succeeded"
        )
        # Sync the proxy with the entity
        self.proxy_sync(entity=entity)


class ProcessCursor(PackageCursor):
    def __init__(self, client):
        super().__init__(client, Process)


class Tool(GenericProxy, ExtrasProxy, TaggableProxy):
    id = Id()
    name = NameId()

    metadata_created = Property(validator=DateField)
    metadata_modified = Property(validator=DateField)
    state = Property(validator=StateField)
    type = Property(validator=StrField)
    creator = Property(validator=UUIDField, entity_name="creator_user_id")

    notes = Property(validator=StrField(nullable=True), updatable=True)
    author = Property(validator=StrField(nullable=True), updatable=True)
    author_email = Property(validator=StrField(nullable=True), updatable=True)
    maintainer = Property(validator=StrField(nullable=True), updatable=True)
    maintainer_email = Property(validator=StrField(nullable=True), updatable=True)

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

    # resources = RefList(Resource, trigger_sync=True)
    organization = Reference(
        "Organization",
        entity_name="owner_org",
        create_default="default_organization",
        updatable=True,
        trigger_sync=True,
    )

    # images = RefList("Image", trigger_sync=False)

    groups = RefList("Group", trigger_sync=False)
    extras = ExtrasProperty()
    tags = TagList()


class ToolCursor(PackageCursor):
    def __init__(self, client):
        super().__init__(client, Tool)
