from .base import BaseAPI
from .dataset import DatasetCursor
from .generic import GenericCursor, api_call
from .group import Group, Organization
from .resource import ResourceCursor
from .user import UserCursor
from .vocab import TagCursor, VocabularyCursor


class CatalogAPI(BaseAPI):
    """
    CatalogAPI is a superclass of the STELAR Python Client. It implements
    data catalog handling methods that utilizes a subset of the available STELAR API
    Endpoints that are related to catalog management operations (Publishing,
    Searching etc.).

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create the cursors for the various catalog entities
        self.datasets = DatasetCursor(self)
        self.resources = ResourceCursor(self)
        self.organizations = GenericCursor(self, Organization)
        self.groups = GenericCursor(self, Group)
        self.vocabularies = VocabularyCursor(self)
        self.users = UserCursor(self)
        self.tags = TagCursor(self)

    def fetch_active_vocabularies(self):
        """Return a list of dicts with the id and name of each tag vocabulary.

        This function is usually called to update the vocabulary index inside the
        client, and is not very useful to end users.
        """
        ac = api_call(self)
        return ac.vocabulary_fetch()
