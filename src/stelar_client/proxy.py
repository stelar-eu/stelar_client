from __future__ import annotations


class ProxyObj:
    """Base class for all proxy objects of the STELAR entities.
    """
    def __init__(self):
        self.obj = None
    
    def proxy_read(self, id):
        raise NotImplementedError
    
    def proxy_update(self, updates: dict):
        raise NotImplementedError


class ProxyProperty:
    """A Python descriptor for implementing access and updating of
       fields of proxy objects.
    """
    def __init__(self, updatable=False, isId=False):
        """Constructs a proxy proerty descriptor"""
        self.updatable = updatable and not isId
        self.types = object
        self.owner = self.name = None

    def __set_name__(self, owner, name):
        assert issubclass(owner, ProxyObj)
        self.owner = owner
        self.name = name

    def __get__(self, obj, objtype=None):
        pass

    def __set__(self, obj, value):
        pass

