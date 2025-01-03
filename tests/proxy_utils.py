from uuid import uuid4
from stelar_client.proxy import Proxy, Registry, RegistryCatalog


class TPRegistry(Registry):
    def __init__(self, catalog, proxy_type):
        super().__init__(catalog, proxy_type)
    def fetch(self, eid=None):
        if eid is None:
            eid = uuid4()
        return self.proxy_type(self, eid)

class TPCatalog(RegistryCatalog):
    def registry_for(self, cls):
        if cls not in self.registry_catalog:
            self.add_registry_for(cls, TPRegistry(self, cls))
        return super().registry_for(cls)


##################################################
#  An 'abstract' subclass of ProxyObj which does
#  not implement an entity.
##################################################
class ProxyTestObj(Proxy, entity=False):

    data = {}
    patch = {}

    def proxy_sync(self, entity=None):
        myid = self.proxy_id
        if self.proxy_changed is not None:
            entity = self.proxy_to_entity()
            self.data[myid] = entity
            self.patch[myid] = self.proxy_to_entity(self.proxy_changed)
            self.proxy_changed = None

        if entity is None:
            entity = self.data[myid]

        self.proxy_from_entity(entity)
