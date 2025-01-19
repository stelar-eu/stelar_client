"""A module containing useful definitions related to STELAR API entities
"""


class MissingParametersError(Exception):
    pass


class DuplicateEntryError(Exception):
    pass


class STELARUnknownError(Exception):
    pass


class EntityNotFoundError(Exception):
    pass
