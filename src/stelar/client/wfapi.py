from stelar.client.base import BaseAPI, DefaultsRegistry
from stelar.client.generic import GenericCursor
from stelar.client.workflows import Process, ProcessCursor, Task, Workflow


class WorkflowsAPI(BaseAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create the registries
        for ptype in [Process, Task, Workflow]:
            DefaultsRegistry(self, ptype)

    @property
    def processes(self):
        """The processes cursor"""
        return ProcessCursor(self)

    @property
    def tasks(self):
        """The processes cursor"""
        return GenericCursor(self, Task)

    @property
    def workflows(self):
        """The processes cursor"""
        return GenericCursor(self, Workflow)
