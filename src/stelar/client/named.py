from .generic import GenericProxy
from .proxy import ExtrasProxy


class NamedProxy(GenericProxy, ExtrasProxy, entity=False):
    """Proxies for entities with a name which is unique.

    Named proxies include those implemented in CKAN as packages or groups.
    Other entities may have a name atrribute, but it is not unique.
    """

    pass
