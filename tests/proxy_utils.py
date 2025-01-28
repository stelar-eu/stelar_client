from uuid import UUID, uuid4

from stelar.client.proxy import Proxy, ProxySynclist, Registry, RegistryCatalog


class TPRegistry(Registry):
    def __init__(self, catalog, proxy_type):
        super().__init__(catalog, proxy_type)

    def fetch(self, eid=None):
        if eid is None:
            eid = uuid4()
        return self.proxy_type(self, eid)


class TPCatalog(RegistryCatalog):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.vocabs = []

    def fetch_active_vocabularies(self):
        return self.vocabs

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

        if self.proxy_id == UUID(int=0):
            # Populate sync list
            psl = ProxySynclist()
            psl.on_create_proxy(self)

            # Create the entity
            schema = self.proxy_schema
            entity = self.proxy_to_entity()

            # ------------------------------
            # Simulate entity creation

            # 1. Generate an ID
            myid = uuid4()
            entity[schema.id.entity_name] = str(myid)

            # 2. Fill up non-provided values with defaults
            for prop in schema.properties.values():
                if prop.entity_name not in entity:
                    v = prop.validator
                    entity[prop.entity_name] = v.convert_to_entity(
                        v.default_value(),
                        vocindex=self.proxy_registry.catalog.vocabulary_index,
                    )

            self.data[myid] = entity
            # -------------------------------

            # We add this proxy to its registry!
            # This will call proxy_sync recursively !
            self.proxy_registry.register_proxy_for_entity(self, entity)
            self.proxy_from_entity(entity)
            self.proxy_changed = None
            # Sync around
            psl.sync()
            return

        if self.proxy_changed is not None:
            entity = self.proxy_to_entity()
            self.data[myid] = entity
            self.patch[myid] = self.proxy_to_entity(self.proxy_changed)
            self.proxy_changed = None

        if entity is None:
            entity = self.data[myid]

        self.proxy_from_entity(entity)
