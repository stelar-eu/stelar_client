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
from .proxy import ProxyState, deferred_sync
from .resource import Resource
from .user import User
from .vocab import Tag, Vocabulary
from .workflows import Process, Task, Tool, Workflow

__all__ = [
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
    "Workflow",
    "Tool",
    "deferred_sync",
]

# Include all proxy exceptions
from .proxy.exceptions import *
from .proxy.exceptions import __all__ as _exceptions

__all__ += _exceptions
del _exceptions

# Include all utility functions
from .utils import *
from .utils import __all__ as _utils

__all__ += _utils
del _utils
