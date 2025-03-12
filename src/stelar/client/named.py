from .generic import GenericProxy
from .proxy import ExtrasProperty, ExtrasProxy, NameId, Property, StateField, StrField


class NamedProxy(GenericProxy, ExtrasProxy, entity=False):
    """Proxies for entities with a name which is unique.

    Named proxies include those implemented in CKAN as packages or groups.
    Other entities may have a name atrribute, but it is not unique.
    """

    name = NameId()
    state = Property(validator=StateField)
    type = Property(validator=StrField)

    # Named entities have the same 'extras' field (unlike resources)
    extras = ExtrasProperty()
