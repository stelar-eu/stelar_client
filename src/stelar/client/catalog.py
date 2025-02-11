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

    @property
    def datasets(self):
        """The datasets cursor"""
        return DatasetCursor(self)

    @property
    def resources(self):
        """The resources cursor"""
        return GenericCursor(self, Resource)

    @property
    def organizations(self):
        """The organizations cursor"""
        return GenericCursor(self, Organization)

    @property
    def groups(self):
        """The groups cursor"""
        return GenericCursor(self, Group)

    @property
    def vocabularies(self):
        """The vocabulary cursor"""
        return GenericCursor(self, Vocabulary)

    @property
    def users(self):
        """The user cursor"""
        return UserCursor(self)

    @property
    def tags(self):
        """The tag cursor"""
        return TagCursor(self)

    def fetch_active_vocabularies(self):
        """Return a list of dicts with the id and name of each tag vocabulary.

        This function is usually called to update the vocabulary index inside the
        client, and is not very useful to end users.
        """
        ac = api_call(self)
        return ac.vocabulary_fetch()
