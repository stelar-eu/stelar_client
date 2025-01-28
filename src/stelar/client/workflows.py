from __future__ import annotations
from .base import BaseAPI
from .proxy import Proxy


class Task(Proxy):
    """Proxy object for Process tasks.
    """
    def __init__(self, wf: Process, id):
        self.wf = wf
        self.id = id


class ParamObj:
    pass


class TaskSpec:
    """A Process task specification.

    Each task has a specification which describes 
    the tool to execute, its inputs and outputs and 
    the parameters of execution.
    """
    def __init__(self, wf: Process):
        self.wf = wf
        self.__tool = None
        self.__params = ParamObj()
        self.__datasets = ParamObj()
        self.__inputs = ParamObj()
        self.__outputs = ParamObj()


    @property
    def tool(self):
        return self.__tool
    @tool.setter
    def set_tool(self, tool):
        self.__tool = tool

    def exec(self) -> Task:
        raise NotImplementedError


    


class Process(Proxy):
    """Proxy object for workflow processes (executions).
    """

    # Fields
    # workflow_exec_id (execution id)
    # wf_package_id
    # tags.package_id
    # state:  [running, ...]
    # creator [str]
    # start_date
    # end_date


    def __init__(self, wfapi: WorkflowsAPI, id=None):
        self.wfapi = wfapi
        self.id = id


    def create_task(self) -> TaskSpec:
        return Task(self)

    def close(self):
        raise NotImplementedError


class WorkflowsAPI(BaseAPI):
    
    def create_process(self) -> Process:
        """Create a new workflow execution"""
        return Process(self)
    
    def create_task(self) -> Task:
        """Create a new (standalone) worflow execution with an initial task"""
        return Task(Process(self))

