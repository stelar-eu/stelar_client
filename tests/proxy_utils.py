from uuid import uuid4
from stelar_client.proxy import ProxyObj, ProxyProperty, ProxyId, ProxyCache

class TPCache(ProxyCache):
    def __init__(self, proxy_type):
        super().__init__(None, proxy_type)
    def fetch(self, eid=None):
        if eid is None:
            eid = uuid4()
        return self.proxy_type(self, eid)

##################################################
#  An 'abstract' subclass of ProxyObj which does
#  not implement an entity.
##################################################
class ProxyTestObj(ProxyObj, entity=False):

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

