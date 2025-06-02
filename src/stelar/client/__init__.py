from importlib.metadata import PackageNotFoundError, version  # pragma: no cover

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

from .client import Client
from .dataset import Dataset
from .group import Group, Organization
from .process import Process
from .proxy import ProxyState, deferred_sync

# Include all proxy exceptions
from .proxy.exceptions import *
from .proxy.exceptions import __all__ as __all_exceptions
from .resource import Resource
from .task_spec import TaskSpec
from .tasks import Task
from .tool import Tool
from .user import User

# Include all utility functions
from .utils import *
from .utils import __all__ as __all_utils
from .vocab import Tag, Vocabulary
from .workflows import Workflow

__all__ = [
    *__all_exceptions,
    *__all_utils,
    "Client",
    "Dataset",
    "Resource",
    "Organization",
    "Group",
    "ProxyState",
    "Tag",
    "Vocabulary",
    "User",
    "Process",
    "Task",
    "TaskSpec",
    "Workflow",
    "Tool",
    "deferred_sync",
]

del __all_exceptions
del __all_utils

import os

if os.getenv("SPHINX_BUILD"):
    # This prevents duplicate documentation by sphinx
    del __all__
