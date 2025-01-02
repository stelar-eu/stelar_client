from .base import BaseAPI
from .endpoints import APIEndpointsV1
from .model import MissingParametersError, STELARUnknownError, DuplicateEntryError, EntityNotFoundError
from .proxy import Registry
from .apicall import GenericCursor
from .dataset import Dataset
from .resource import Resource
from .organization import Organization
from .group import Group
from requests.exceptions import HTTPError
from urllib.parse import urljoin, urlencode


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
        dataset_registry = Registry(self, Dataset)
        resource_registry = Registry(self, Resource)
        organization_registry = Registry(self, Organization)
        group_registry = Registry(self, Group)

    @property
    def datasets(self):
        """The datasets cursor"""
        return GenericCursor(self, Dataset)

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

    