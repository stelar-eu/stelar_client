"""Basic support for tasks in the client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generator
from uuid import UUID

from .dataset import Dataset
from .group import Organization
from .resource import Resource
from .utils import convert_proxy_id_to_str

if TYPE_CHECKING:
    # Type definitions for
    from .tool import Tool

    ToolSpec = Tool | UUID | str | None
    ImageSpec = str | None
    ExistingDataset = Dataset | UUID | str


class TaskSpec:
    """A task spec is used to create tasks.

    Contrary to other entities, Task creation is more complicated than simply
    providing values for some scalar attributes. Tasks, once created are
    not really editable; therefore, all task fields must be specified
    at task creation time.

    This class helps by collecting arguments needed to initialize a new Task.
    """

    def __init__(
        self, tool: ToolSpec = None, *, image: ImageSpec = None, name: str = None
    ):
        from .tool import Tool

        self.tool = convert_proxy_id_to_str(tool, Tool)
        if isinstance(image, str | None):
            self.image = image
        else:
            raise TypeError("Expected a string as image")

        if not isinstance(name, str | None):
            raise TypeError("Expected a string as name")

        self.name = name
        self.datasets = {}
        self.inputs = {}
        self.outputs = {}
        self.parameters = {}

    @classmethod
    def from_json(cls, json_spec: dict) -> TaskSpec:
        """Create a TaskSpec from a JSON specification.

        Args:
            json_spec (dict): the JSON specification for the task spec.
        """
        tool = json_spec.get("tool")
        image = json_spec.get("image")
        name = json_spec.get("name", "task")

        ts = cls(tool=tool, image=image, name=name)
        ts.datasets = json_spec.get("datasets", {})
        ts.inputs = json_spec.get("inputs", {})
        ts.outputs = json_spec.get("outputs", {})
        ts.parameters = json_spec.get("parameters", {})

        return ts

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
            self.datasets[alias] = convert_proxy_id_to_str(dset, Dataset)
        else:
            if "name" not in dspec:
                raise ValueError("A dataset spec must provide a name")
            if "owner_org" not in dspec:
                dspec["owner_org"] = "stelar-klms"
            else:
                dspec["owner_org"] = convert_proxy_id_to_str(
                    dspec["owner_org"], Organization, nullable=False
                )
            self.datasets[alias] = dspec

        return self

    def process_inspec_entry(
        self, inspec: str | UUID | Resource | list[str | UUID | Resource]
    ) -> Generator[str]:
        if isinstance(inspec, (Resource, UUID, str)):
            yield convert_proxy_id_to_str(inspec, Resource)
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
                case {"url": url, "resource": res}:
                    return {
                        "url": url,
                        "resource": convert_proxy_id_to_str(res, Resource),
                    }
                case {"url": url}:
                    return outspec
                case _:
                    raise ValueError("Bad format for output spec", outspec)
        else:
            raise TypeError(
                f"Bad type {type(outspec)} for output spec, expected string or dict"
            )

    def o(self, **ospec) -> TaskSpec:
        for name, osp in ospec.items():
            self.outputs[name] = self.process_outspec(osp)
        return self

    def p(self, **params) -> TaskSpec:
        self.parameters |= params
        return self

    def spec(self) -> dict:
        """Return the task spec as a dictionary.

        Returns:
            dict: the task spec as a dictionary.
        """
        s = {}

        if self.tool is not None:
            s["tool"] = self.tool

        if self.image is not None:
            s["image"] = self.image

        s["datasets"] = self.datasets.copy()
        s["inputs"] = self.inputs.copy()
        s["outputs"] = self.outputs.copy()
        s["parameters"] = self.parameters.copy()
        s["name"] = self.name if self.name is not None else "unnamed"
        return s
