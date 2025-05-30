from __future__ import annotations

from .api_call import api_call
from .package import PackageCursor, PackageProxy
from .proxy import DateField, Property, Reference, RefList, StrField
from .proxy.fieldvalidation import EnumeratedField
from .task_spec import TaskSpec
from .tasks import Task
from .utils import client_for


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

    def run(self, task_spec: TaskSpec, secrets=None) -> Task:
        """Create a new Task in this process"""
        return client_for(self).tasks.create(self.id, task_spec, secrets=secrets)


class ProcessCursor(PackageCursor[Process]):
    def __init__(self, client):
        super().__init__(client, Process)
