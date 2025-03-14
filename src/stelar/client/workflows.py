from __future__ import annotations

from .api_call import api_call
from .generic import GenericProxy
from .package import PackageCursor, PackageProxy
from .proxy import DateField, Id, Property, Reference, RefList, StrField
from .proxy.fieldvalidation import EnumeratedField
from .proxy.property import DictProperty, ListProperty
from .utils import client_for


class Workflow(PackageProxy):
    title = Property(validator=StrField, updatable=True)
    version = Property(
        validator=StrField(nullable=True, maximum_len=100), updatable=True
    )

    repository = Property(validator=StrField(nullable=True), updatable=True)
    executor = Property(validator=StrField(nullable=True), updatable=True)
    # resources = RefList(Resource, trigger_sync=True)


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


class Process(PackageProxy):
    """Proxy object for workflow processes (executions)."""

    # Currently, the STELAR API redefines the 'creator' field to return
    # the username of the creator, rather than the user ID. This is a
    # temporary workaround until the API is updated to return the user ID.
    creator = Property(validator=StrField, entity_name="creator")

    # These are all non-CKAN properties in the STELAR API
    workflow = Reference(
        "Workflow",
        updatable=True,
        nullable=True,
        entity_name="workflow",
        trigger_sync=False,
    )
    tasks = RefList("Task", trigger_sync=True)

    start_date = Property(validator=DateField, updatable=False)
    end_date = Property(validator=DateField, updatable=True)
    exec_state = Property(validator=ExecStateField, updatable=False)

    title = Property(validator=StrField, updatable=True)
    version = Property(
        validator=StrField(nullable=True, maximum_len=100), updatable=True
    )
    url = Property(validator=StrField(nullable=True), updatable=True)

    # resources = RefList(Resource, trigger_sync=True)
    #
    # TODO
    #  tasks

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


class ProcessCursor(PackageCursor[Process]):
    def __init__(self, client):
        super().__init__(client, Process)


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

    # images = RefList("Image", trigger_sync=False)


class ToolCursor(PackageCursor[Tool]):
    def __init__(self, client):
        super().__init__(client, Tool)
