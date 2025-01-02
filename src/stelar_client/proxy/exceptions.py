#----------------------------------------------------------
# Exceptions raised by the proxy system.
#----------------------------------------------------------


class EntityError(ValueError):
    """Raised when the system encounters a malformed entity"""
    pass

class ProxyError(RuntimeError):
    """The proxying state is not consistent or an illegal proxying command was issued"""
    pass

class ConflictError(ProxyError):
    """Update for an entity with unsynchronized changes"""
    pass

class InvalidationError(ProxyError):
    """Invalidation attempt on dirty proxy"""
    pass

class ProxyOperationError(ProxyError):
    """An error occurred during an API operation"""
    def __init__(self, /, proxy_type, eid, operation, *args, **kwargs):
        self.proxy_type = proxy_type
        self.eid = eid
        self.operation = operation
        super().__init__(*args, **kwargs)
    def __repr__(self):
        typename = self.proxy_type.__name__
        return f"ProxyOperationError({self.operation} {typename} {self.eid} {self.args})"