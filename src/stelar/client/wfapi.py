from .base import BaseAPI
from .generic import GenericCursor
from .package import PackageCursor
from .workflows import ProcessCursor, Task, ToolCursor, Workflow


class WorkflowsAPI(BaseAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processes = ProcessCursor(self)
        self.tasks = GenericCursor(self, Task)
        self.workflows = PackageCursor(self, Workflow)
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
