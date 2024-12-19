from typing import List, Dict
from IPython.core.display import HTML
from IPython.display import display


class MissingParametersError(Exception):
    pass

class DuplicateEntryError(Exception):
    pass

class STELARUnknownError(Exception):
    pass

class EntityNotFoundError(Exception):
    pass