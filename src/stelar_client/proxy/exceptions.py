#----------------------------------------------------------
# Exceptions raised by the proxy system.
#----------------------------------------------------------


class EntityError(ValueError):
    """Raised when the system encounters a malformed entity"""
    pass

class ProxyError(RuntimeError):
    """The proxying state is not consistent or an illegal proxying command was issued"""
    pass

class InvalidationError(ProxyError):
    """Invalidation attempt on dirty proxy"""
    pass
