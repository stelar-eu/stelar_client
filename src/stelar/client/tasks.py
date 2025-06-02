"""Basic support for tasks in the client."""

from __future__ import annotations

import time
from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING
from uuid import UUID

from .api_call import api_call
from .dataset import Dataset
from .generic import GenericCursor, GenericProxy, GenericProxyList
from .proxy import (
    DateField,
    Id,
    Property,
    ProxySynclist,
    Reference,
    StrField,
    derived_property,
)
from .proxy.property import DictProperty
from .utils import client_for

if TYPE_CHECKING:
    # Type definitions for
    from .workflows import Tool

    ToolSpec = Tool | UUID | str | None
    ImageSpec = str | None
    ExistingDataset = Dataset | UUID | str


class Task(GenericProxy):
    id = Id(entity_name="id")
    start_date = Property(validator=DateField)
    end_date = Property(validator=DateField(nullable=True))

    exec_state = Property(validator=StrField)

    creator = Property(validator=StrField, entity_name="creator")
    process = Reference("Process", entity_name="process_id", trigger_sync=True)

    messages = Property(validator=StrField, updatable=False, optional=True)

    # TODO: parameters are dict[str, json]
    parameters = DictProperty(str, str, updatable=False, optional=True)
    metrics = DictProperty(str, str, updatable=False, optional=True)

    inputs = DictProperty(str, list[str], updatable=False, optional=True)
    outputs = DictProperty(str, dict, updatable=False, optional=True)

    tool = Property(validator=StrField, optional=True)
    image = Property(validator=StrField, optional=True)

    # TODO: return the tool proxy
    # via a method

    tags = DictProperty(str, str, updatable=False, optional=True)

    @derived_property
    def is_external(self, entity) -> bool:
        """Check if this task is local (i.e., not using a remote tool)."""
        return "image" not in entity

    @derived_property
    def done(self, entity) -> bool:
        """Check if this task is done (i.e., has an end date)."""
        return entity["end_date"] is not None

    def sync_state(self):
        self.proxy_sync()
        """Check if this task is done (i.e., has an end date)."""
        return self.exec_state

    def wait(self, timeout: float = 5.0, polling_interval: float = 1.0):
        """Wait for the task to finish.

        Args:
            timeout (float): The maximum time to wait in seconds. Defaults to 5.0.
            polling_interval (float): The interval between checks in seconds. Defaults to 1.0.
        """
        while self.sync_state() not in ("succeeded", "failed") and timeout > 0:
            time.sleep(polling_interval)
            timeout -= polling_interval
        return self.exec_state in ("succeeded", "failed")

    @derived_property
    def runtime(self, entity) -> float | None:
        """Calculate the runtime of the task in seconds.

        Returns:
            float: The runtime in seconds, or None if the task is not done.
        """
        start_date = datetime.fromisoformat(entity["start_date"])
        end_date = (
            datetime.fromisoformat(entity["end_date"])
            if entity["end_date"] is not None
            else datetime.now()
        )
        return (end_date - start_date).total_seconds()

    @cached_property
    def signature(self) -> str:
        """Fetch the signature for this task.

        The signature is a unique identifier for the task, which allows calling
        methods `job_input()` and `exit_job()` to implement an external task,
        even from a connection that is not authenticated.
        """
        return api_call(self).task_signature(str(self.id))["signature"]

    @cached_property
    def job_input(self, signature=None) -> dict:
        """Return the job input for this local task.

        The job input is a dictionary that contains the inputs and parameters
        of the task, formatted for use in a job execution context.
        """
        if not self.is_external:
            raise ValueError("Cannot get job input for non-external tasks")

        if signature is None:
            signature = self.signature
            if signature is None:
                raise ValueError(
                    "No signature, cannot get job input for a task without a signature"
                )

        return api_call(self).task_job_input(task_id=str(self.id), signature=signature)

    def exit_job(
        self,
        *,
        metrics={},
        output={},
        message="The task is finished",
        status="succeeded",
        signature=None,
    ):
        """Post the job output for this external task.

        The job output contains the outputs and metrics of the task,
        the final message and a task status.

        Args:
            metrics (dict): A dictionary of metrics to post.
            output (dict): A dictionary of outputs to post.
            message (str): A message to post with the job output.
            status (str): The status of the task, e.g., "succeeded" or "failed".
            signature (str, optional): The signature of the task. If not provided,
                the signature will be fetched.
        Raises:
            ValueError: If the task is not external or if the POST request fails.

        """
        if not self.is_external:
            raise ValueError("Cannot post job output for non-external tasks")
        if signature is None:
            signature = self.signature
            if signature is None:
                raise ValueError(
                    "No signature, cannot post job output for a task without a signature"
                )

        output_spec = {
            "metrics": metrics,
            "output": output,
            "message": message,
            "status": status,
        }

        psl = ProxySynclist([self])
        api_call(self).task_post_job_output(str(self.id), signature, output_spec)
        psl.on_update_all(self)
        psl.sync()

    def fail(
        self,
        message: str,
        *,
        metrics={},
        output={},
    ):
        """Mark this external task as failed with a message.

        This method sets the task's execution state to 'failed' and updates
        the messages property with the provided message.
        """
        return self.exit_job(
            metrics=metrics, output=output, message=message, status="failed"
        )

    def abort(self, message: str = None):
        """Abort this task.

        This method sets the task's execution state to 'failed' and updates
        the messages property with the provided message.
        """
        if message is None:
            c = client_for(self)
            message = f"Task was aborted by user {c.users.current_user.username} at {datetime.now().isoformat()}"

        output_spec = {
            "message": message,
            "status": "failed",
        }

        psl = ProxySynclist([self])
        api_call(self).task_post_job_output(str(self.id), self.signature, output_spec)
        psl.sync()

    def jobs(self):
        """Return a dictionary with info about Kubernetes jobs for this task."""
        response = client_for(self).GET("v2/task", self.id, "jobs")
        response.raise_for_status()
        return response.json()["result"]

    def logs(self):
        """Return the logs for this task."""
        response = client_for(self).GET("v2/task", self.id, "logs")
        response.raise_for_status()
        return response.json()["result"]

    def printlog(self, *, file=None, flush=False):
        for job, log in self.logs().items():
            print(job, ":", file=file, flush=flush)
            print(log, file=file, flush=flush)


class TaskCursor(GenericCursor):
    """A cursor for a collection of STELAR tasks."""

    def __init__(self, api):
        super().__init__(api, Task)

    def fetch(self, **kwargs):
        raise NotImplementedError("TaskCursor does not support fetch operations.")

    def fetch_list(
        self, *, state="created", limit: int = 100, offset: int = 0
    ) -> list[Task]:
        """Fetch a list of tasks in a specific state.

        Args:
            state (str): The state of the tasks to fetch. Defaults to 'running'.
            **kwargs: Additional keyword arguments to pass to the API call.
        Returns:
            list[Task]: A list of Task objects in the specified state.
        """
        ac = api_call(self)
        tasks = ac.task_list(state=state, limit=limit, offset=offset)
        flat_tasks = []

        if tasks:  # Note : tasks is a dict with keys for each state, or None!!
            for s in ("created", "running", "succeeded", "failed"):
                flat_tasks.extend(tasks.get(s, []))

        return GenericProxyList(flat_tasks, client_for(self), self.proxy_type)

    def created(self, *, limit: int = 100, offset: int = 0) -> list[Task]:
        """Fetch a list of tasks in the 'created' state.

        Args:
            limit (int): The maximum number of tasks to fetch. Defaults to 100.
            offset (int): The offset for pagination. Defaults to 0.
        Returns:
            list[Task]: A list of Task objects in the 'created' state.
        """
        return self.fetch_list(state="created", limit=limit, offset=offset)

    def running(self, *, limit: int = 100, offset: int = 0) -> list[Task]:
        """Fetch a list of tasks in the 'running' state.

        Args:
            limit (int): The maximum number of tasks to fetch. Defaults to 100.
            offset (int): The offset for pagination. Defaults to 0.
        Returns:
            list[Task]: A list of Task objects in the 'running' state.
        """
        return self.fetch_list(state="running", limit=limit, offset=offset)

    def succeeded(self, *, limit: int = 100, offset: int = 0) -> list[Task]:
        """Fetch a list of tasks in the 'succeeded' state.

        Args:
            limit (int): The maximum number of tasks to fetch. Defaults to 100.
            offset (int): The offset for pagination. Defaults to 0.
        Returns:
            list[Task]: A list of Task objects in the 'succeeded' state.
        """
        return self.fetch_list(state="succeeded", limit=limit, offset=offset)

    def failed(self, *, limit: int = 100, offset: int = 0) -> list[Task]:
        """Fetch a list of tasks in the 'failed' state.

        Args:
            limit (int): The maximum number of tasks to fetch. Defaults to 100.
            offset (int): The offset for pagination. Defaults to 0.
        Returns:
            list[Task]: A list of Task objects in the 'failed' state.
        """
        return self.fetch_list(state="failed", limit=limit, offset=offset)

    def create(self, process_id: UUID | str, task_spec: TaskSpec, secrets=None) -> Task:
        """Create a new Task using the provided TaskSpec.

        Args:
            process_id (UUID): The ID of the process to which the task belongs.
            task_spec (TaskSpec): The specification for the task to create.
            secrets (dict, optional): Secrets to pass to the task.
        Returns:
            Task: The created task.
        """
        json_spec = task_spec.spec()
        json_spec["process_id"] = str(process_id)
        if secrets is not None:
            json_spec["secrets"] = secrets
        ac = api_call(self)
        resp = ac.task_create(**json_spec)
        task_id = resp["id"]
        task = self.fetch_proxy(UUID(task_id))

        psl = ProxySynclist()
        psl.on_create_proxy(task)
        psl.sync()
        return task
