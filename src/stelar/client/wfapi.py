from .base import BaseAPI
from .package import PackageCursor
from .process import ProcessCursor
from .tasks import TaskCursor
from .tool import ToolCursor
from .workflows import Workflow


class WorkflowsAPI(BaseAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processes = ProcessCursor(self)
        self.tasks = TaskCursor(self)
        self.workflows = PackageCursor(self, Workflow)
        self.tools = ToolCursor(self)
