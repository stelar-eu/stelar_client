from .base import BaseAPI, DefaultsRegistry
from .dataset import Dataset, DatasetCursor
from .generic import GenericCursor, api_call
from .group import Group, Organization
from .resource import Resource
from .user import User, UserCursor
from .vocab import Tag, TagCursor, Vocabulary


class CatalogAPI(BaseAPI):
    """
    CatalogAPI is a superclass of the STELAR Python Client. It implements
    data catalog handling methods that utilizes a subset of the available STELAR API
    Endpoints that are related to catalog management operations (Publishing,
    Searching etc.).

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create the registries
        for ptype in [
            Dataset,
            Resource,
            Organization,
            Group,
            Vocabulary,
            Tag,
            User,
        ]:
            DefaultsRegistry(self, ptype)

        self.datasets = DatasetCursor(self)
        self.resources = GenericCursor(self, Resource)
        self.organizations = GenericCursor(self, Organization)
        self.groups = GenericCursor(self, Group)
        self.vocabularies = GenericCursor(self, Vocabulary)
        self.users = UserCursor(self)
        self.tags = TagCursor(self)

    def fetch_active_vocabularies(self):
        """Return a list of dicts with the id and name of each tag vocabulary.

        This function is usually called to update the vocabulary index inside the
        client, and is not very useful to end users.
        """
        ac = api_call(self)
        return ac.vocabulary_fetch()
