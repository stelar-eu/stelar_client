from stelar.client.base import BaseAPI, DefaultsRegistry
from stelar.client.generic import GenericCursor
from stelar.client.workflows import (
    Process,
    ProcessCursor,
    Task,
    Tool,
    ToolCursor,
    Workflow,
)


class WorkflowsAPI(BaseAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create the registries
        for ptype in [Process, Task, Workflow, Tool]:
            DefaultsRegistry(self, ptype)
        self.processes = ProcessCursor(self)
        self.tasks = GenericCursor(self, Task)
        self.workflows = GenericCursor(self, Workflow)
        self.tools = ToolCursor(self)


class TaskSpec:
    """This is a base class for defining new task specifications"""

    def __init__(self, tool=None, datasets={}, inputs={}, outputs={}, parameters={}):
        self._tool = tool
        self._datasets = datasets
        self._inputs = inputs
        self._outputs = outputs
        self._parameters = parameters

    def spec(self):
        return {
            "tool_name": self._tool["name"],
            "docker_image": self._tool["docker_image"],
            "datasets": self._datasets,
            "inputs": self._inputs,
            "outputs": self._outputs,
            "parameters": self._parameters,
        }
