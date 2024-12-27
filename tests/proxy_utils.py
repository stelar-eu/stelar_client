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
    old_data = {}

    def proxy_fetch(self):
        myid = self.proxy_schema.get_id(self)
        return self.data[myid]

    def proxy_update(self, new_data, old_data):
        myid = self.proxy_schema.get_id(self)
        self.data[myid] = new_data
        self.old_data[myid] = old_data
        return new_data

