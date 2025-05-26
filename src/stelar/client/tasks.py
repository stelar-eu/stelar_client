"""Basic support for tasks in the client.
"""
from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Generator
from uuid import UUID

from .api_call import api_call
from .dataset import Dataset
from .generic import GenericCursor, GenericProxy
from .group import Organization
from .proxy import DateField, Id, Property, Reference, StrField, derived_property
from .proxy.property import DictProperty, ListProperty
from .resource import Resource
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
    process = Reference("Process", entity_name="process_id", trigger_sync=False)

    messages = Property(validator=StrField, updatable=False, optional=True)

    # TODO: parameters are dict[str, json]
    parameters = DictProperty(str, str, updatable=False, optional=True)
    metrics = DictProperty(str, str, updatable=False, optional=True)

    inputs = DictProperty(str, list[str], updatable=False, optional=True)
    outputs = ListProperty(dict, updatable=False, optional=True)

    tool = Property(validator=StrField, optional=True)
    image = Property(validator=StrField, optional=True)

    # TODO: return the tool proxy
    # via a method

    tags = DictProperty(str, str, updatable=False, optional=True)

    @derived_property
    def is_external(self, entity) -> bool:
        """Check if this task is local (i.e., not using a remote tool)."""
        return "image" not in entity

    @property
    def signature(self) -> str:
        """Return a string signature for this task."""
        return client_for(self).local_task_sigs.get(str(self.id))

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

        api_call(self).task_post_job_output(str(self.id), signature, output_spec)
        self.proxy_sync()

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


class TaskSpec:
    """A task spec is used to create tasks.

    Contrary to other entities, Task creation is more complicated than simply
    providing values for some scalar attributes. Tasks, once created are
    not really editable; therefore, all task fields must be specified
    at task creation time.

    This class helps by collecting arguments needed to initialize a new Task.
    """

    def __init__(
        self, tool: ToolSpec = None, *, image: ImageSpec = None, name: str = "task"
    ):
        from .workflows import Tool

        if isinstance(tool, Tool):
            self.tool = str(tool.name)
        elif isinstance(tool, UUID):
            self.tool = str(tool)
        elif isinstance(tool, str | None):
            self.tool = tool
        else:
            raise TypeError("Expected a Tool proxy or a string, or None")

        if isinstance(image, str | None):
            self.image = image
        else:
            raise TypeError("Expected a string as image")

        if not isinstance(name, str):
            raise TypeError("Expected a string as name")

        self.name = name
        self.datasets = {}
        self.inputs = {}
        self.outputs = {}
        self.parameters = {}

    def is_external(self) -> bool:
        """Check if this task spec is local (i.e., not using a remote tool)."""
        return self.tool is None and self.image is None

    def d(
        self, alias: str, dset: Dataset | UUID | str | None = None, **dspec
    ) -> TaskSpec:
        """Add a dataset alias in the task spec.

        An alias stands for either an existing dataset or for the
        spec of a future dataset.

        Dataset aliases can be useful in specifying input and output arguments
        to a task.

        Args:
            alias (str): the dataset alias name
            dset  (Dataset|UUID|str|None): specify an existing dataset for this alias
            dspec (dict): the spec for a future dictionary.
        """

        if dset is not None:
            if dspec:
                raise ValueError("Cannot provide both a dataset and a new dataset spec")

            if isinstance(dset, Dataset):
                u = str(dset.id)
            elif isinstance(dset, str):
                u = dset
            elif isinstance(dset, UUID):
                u = str(dset)
            else:
                raise TypeError("Unknown type to specify a Dataset")

            self.datasets[alias] = u

        else:
            if "name" not in dspec:
                raise ValueError("A dataset spec must provide a name")
            if "owner_org" not in dspec:
                dspec["owner_org"] = "stelar-klms"
            if isinstance(dspec["owner_org"], Organization):
                dspec["owner_org"] = str(dspec["owner_org"].id)
            elif isinstance(dspec["owner_org"], UUID):
                dspec["owner_org"] = str(dspec["owner_org"])
            elif not isinstance(dspec["owner_org"], str):
                raise TypeError("Bad type for organization in dataset specification")
            self.datasets[alias] = dspec

        return self

    def process_inspec_entry(
        self, inspec: str | UUID | Resource | list[str | UUID | Resource]
    ) -> Generator[str]:
        if isinstance(inspec, Resource):
            yield str(inspec.id)
        elif isinstance(inspec, str):
            yield inspec
        elif isinstance(inspec, UUID):
            yield str(inspec)
        elif isinstance(inspec, list | tuple):
            for i in inspec:
                yield from self.process_inspec_entry(i)
        else:
            raise TypeError("Unknown type for input spec")

    def process_inspec(self, inspec) -> list[str]:
        return list(self.process_inspec_entry(inspec))

    def i(self, **input_specs):
        for name, inspec in input_specs.items():
            self.inputs[name] = self.process_inspec(inspec)
        return self

    def process_outspec(self, outspec: str | dict):
        # Output is either an S3 URI (str)
        # or a dict. No processing here (yet!)
        if isinstance(outspec, str):
            return {"url": outspec}
        elif isinstance(outspec, dict):
            match outspec:
                case {
                    "url": url,
                    "resource": dict(),
                    "dataset": str(),
                }:
                    return outspec
                case {"url": url, "resource": Resource() as res}:
                    return {"url": url, "resource": str(res.id)}
                case {"url": url, "resource": UUID() as res}:
                    return {"url": url, "resource": str(res)}
                case {"url": url, "resource": str() as res}:
                    return {"url": url, "resource": res}
                case {"url": url}:
                    return outspec
                case _:
                    raise ValueError("Bad format for output spec")
        else:
            raise TypeError("Bad type for output spec, expected string or dict")

    def o(self, **ospec) -> TaskSpec:
        for name, osp in ospec.items():
            self.outputs[name] = self.process_outspec(osp)
        return self

    def p(self, **params) -> TaskSpec:
        self.parameters |= params
        return self

    def spec(self) -> dict:
        s = {}

        if self.tool is not None:
            s["tool"] = self.tool

        if self.image is not None:
            s["image"] = self.image

        s["datasets"] = self.datasets.copy()
        s["inputs"] = self.inputs.copy()
        s["outputs"] = self.outputs.copy()
        s["parameters"] = self.parameters.copy()
        s["name"] = self.name
        return s


class TaskCursor(GenericCursor):
    """A cursor for a collection of STELAR tasks."""

    def __init__(self, api):
        super().__init__(api, Task)

    def fetch(self, **kwargs):
        raise NotImplementedError("TaskCursor does not support fetch operations.")

    def fetch_list(self, **kwargs):
        raise NotImplementedError("TaskCursor does not support fetch operations.")

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
        if resp["job_id"] == "__external__":
            # This is a local task, so we need to handle it differently
            signature = resp["signature"]
            client_for(self).commit_local_task_sig(task_id, signature)
        return self.fetch_proxy(UUID(task_id))
