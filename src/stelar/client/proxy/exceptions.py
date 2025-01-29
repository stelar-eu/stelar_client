# ----------------------------------------------------------
# Exceptions raised by the proxy system.
# ----------------------------------------------------------
__all__ = [
    "EntityError",
    "ConversionError",
    "ProxyError",
    "InvalidationError",
    "ConflictError",
    "ErrorState",
    "ProxyOperationError",
    "EntityNotFound",
]


class EntityError(ValueError):
    """Raised when the system encounters a malformed entity"""

    pass


class ConversionError(EntityError):
    """A problem with conversion to and from entity"""

    def __init__(self, property, conv_type):
        super().__init__(
            f"Conversion failed for {property} {conv_type}", property.name, conv_type
        )


class ProxyError(RuntimeError):
    """The proxying state is not consistent or an illegal proxying command was issued"""

    pass


class ConflictError(ProxyError):
    """Update for an entity with unsynchronized changes"""

    def __init__(self, conflicted_proxy, new_entity, *args):
        super().__init__(*args)
        self.conflicted_proxy = conflicted_proxy
        self.new_entity = new_entity


class InvalidationError(ProxyError):
    """Invalidation attempt on dirty proxy"""

    pass


class ErrorState(ProxyError):
    """Operation on proxy in ERROR state"""

    pass


class ProxyOperationError(ProxyError):
    """An error occurred during an API operation"""

    def __init__(self, /, proxy_type, eid, operation, *args, **kwargs):
        if isinstance(proxy_type, type):
            self.proxy_type = proxy_type.__name__
        else:
            self.proxy_type = str(proxy_type)
        self.eid = str(eid)
        self.operation = operation
        super().__init__(*args, **kwargs)

    def __repr__(self):
        typename = self.proxy_type.__name__
        return f"{self.__class__.__name__}({self.operation} {typename} {self.eid} {self.args})"


class EntityNotFound(ProxyOperationError):
    """Indicate that an entity is not found"""

    def __init__(self, /, proxy_type, eid, operation):
        super().__init__(proxy_type, eid, operation)
