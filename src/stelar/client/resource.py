from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any
from uuid import UUID

from .generic import GenericCursor, GenericProxy, generic_proxy_sync
from .mutils import is_s3url, s3spec_to_url
from .pdutils import read_dataframe
from .proxy import (
    DateField,
    ExtrasProperty,
    Id,
    IntField,
    Property,
    Proxy,
    ProxyVec,
    Reference,
    StrField,
)
from .proxy.refs import RefField
from .reprstyle import resource_to_html
from .utils import client_for

if TYPE_CHECKING:
    from .mutils import S3ObjSpec


class ExtrasResourceProperty(ExtrasProperty):
    """The handling of extras is different for Resource entities."""

    # The format is that extra attributes appear normally in
    # resource entities; there is no extras attribute.

    def convert_entity_to_proxy(self, proxy: Proxy, entity: Any, **kwargs):
        # to recognize extras fields, use the schema
        all_fields = proxy.proxy_schema.all_entity_fields
        proxy_extras = {p: v for p, v in entity.items() if p not in all_fields}
        proxy.proxy_attr[self.name] = proxy_extras

    def convert_proxy_to_entity(self, proxy: Proxy, entity: dict, **kwargs):
        proxy_extras = proxy.proxy_attr[self.name]
        entity |= proxy_extras

    def convert_to_create(
        self, proxy_type, create_props: dict, entity_props: dict, **kwargs
    ):
        all_fields = proxy_type.proxy_schema.all_fields

        # Collect all entries that do not appear in the schema
        entity_extras = {p: v for p, v in create_props.items() if p not in all_fields}
        entity_props |= entity_extras


class PackageField(RefField):
    """A field validator for package references."""

    @property
    def proxy_type(self):
        """Return the proxy type for the package reference."""
        return self.ref_property.proxy_types


class PackageRef(Reference):
    """A polymprphic reference to a package entity, used in Resource."""

    VALIDATOR_CLASS = PackageField

    # All entities with resources
    ENTITIES = ("Dataset", "Process", "Tool", "Workflow")

    def __init__(self):
        super().__init__(
            proxy_type="Dataset",
            nullable=False,
            trigger_sync=True,
            entity_name="package_id",
            updatable=False,
        )

    @cached_property
    def proxy_types(self):
        """Return the proxy types that this reference can point to."""
        from .proxy.schema import Schema

        return tuple(Schema.for_entity(t).cls for t in self.ENTITIES)

    def registry_for(self, obj) -> Any:
        """Return the registry for the package reference, given owner."""
        # Use the package_type attribute to determine the type of package.
        if (
            obj.proxy_attr
            and "_extras" in obj.proxy_attr
            and "package_type" in obj.proxy_attr["_extras"]
        ):
            package_type = obj.proxy_attr["_extras"].get("package_type", "dataset")
        else:
            package_type = "dataset"

        return obj.proxy_registry.catalog.registry_for(package_type.capitalize())


class Resource(GenericProxy):
    """
    A proxy for a STELAR resource with metadata and additional details.
    """

    id = Id()

    # dataset = Reference("Dataset", entity_name="package_id", trigger_sync=True)
    dataset = PackageRef()

    position = Property(validator=IntField)
    state = Property(validator=StrField)
    metadata_modified = Property(validator=DateField)

    url = Property(validator=StrField, updatable=True)
    format = Property(validator=StrField, updatable=True)
    description = Property(validator=StrField, updatable=True)
    hash = Property(validator=StrField, updatable=True)

    name = Property(validator=StrField, updatable=True)
    resource_type = Property(validator=StrField, updatable=True)
    mimetype = Property(validator=StrField, updatable=True)
    mimetype_inner = Property(validator=StrField, updatable=True)
    cache_url = Property(validator=StrField, updatable=True)
    size = Property(validator=IntField, updatable=True)
    created = Property(validator=DateField, updatable=True)
    last_modified = Property(validator=DateField, updatable=True)
    cache_last_updated = Property(validator=DateField, updatable=True)
    url_type = Property(validator=StrField, updatable=True)

    _extras = ExtrasResourceProperty()

    def __getattr__(self, attr):
        try:
            return self.proxy_schema.extras.get(self)[attr]
        except KeyError as e:
            raise AttributeError(attr) from e

    def __setattr__(self, attr, value):
        if attr.startswith("proxy_") or attr in self.proxy_schema.all_fields:
            return object.__setattr__(self, attr, value)

        prop = self.proxy_schema.extras

        # TODO: value validation: It is not clear what to do, presumably the correct
        # value would be transformable to json

        prop.touch(self)
        self.proxy_schema.extras.get(self)[attr] = value
        self.proxy_autocommit()

    def __delattr__(self, attr):
        if attr.startswith("proxy_") or attr in self.proxy_schema.all_fields:
            return object.__delattr__(self, attr)

        prop = self.proxy_schema.extras
        extras = prop.get(self)
        if attr in extras:
            prop.touch(self)
            del extras[attr]
            self.proxy_autocommit()
        else:
            raise AttributeError(attr)

    def proxy_sync(self, entity=None):
        return generic_proxy_sync(self, entity, update_method="update")

    def __str__(self):
        """
        Provide a human-readable string representation of the Resource instance.

        Returns:
            str: A string describing the resource's key attributes.
        """
        return f"Resource ID: {self.id} | Name: {self.name} | URL: {self.url} | Format : {self.format}"

    def _repr_html_(self):
        """
        Provide an HTML representation of the Resource instance for Jupyter display,
        with enhanced styles, watermark, and consistent formatting.
        """
        return resource_to_html(self)

    def open(self, mode="rb", **kwargs):
        """
        Open the resource for reading or writing.

        Args:
            mode (str): The mode in which to open the resource. This can be one of the
                following: 'r', 'rb', 'w', 'wb', 'a', 'ab'.

        Returns:
            file-like: A file-like object that can be used to read or write data.
        """
        client = client_for(self)
        url = self.url
        if not is_s3url(url):
            raise ValueError("Only s3 URLs are supported for path")
        return client.s3fs_open(url, mode=mode, **kwargs)

    def read_dataframe(self, format=None, **kwargs):
        """
        Read a DataFrame from the resource.

        Args:
            format (str): The format of the file to read. If not specified, the format will be
                inferred from the file extension.
            kwargs (dict): Additional keyword arguments to pass to the read.

        Returns:
            pd.DataFrame: The DataFrame read from the resource.
        """
        client = client_for(self)
        format = format or self.format or None
        return read_dataframe(client, self.url, format=format, **kwargs)


class ResourceCursor(GenericCursor):
    """
    A cursor for a collection of STELAR resources.
    """

    def __init__(self, api):
        super().__init__(api, Resource)

    def fetch(self, **kwargs):
        raise NotImplementedError("ResourceCursor does not support fetch operations.")

    def fetch_list(self, **kwargs):
        raise NotImplementedError("ResourceCursor does not support fetch operations.")

    def search_url(self, path: str) -> ProxyVec:
        """Return resources whose url matches the given string.

        Args:
            path (str): The partial URL to search for.
        Returns:
            ProxyVec: A vector of resources with matching URLs.
        """
        res = self.search(query=[f"url:{path}"])
        rl = [UUID(r["id"]) for r in res["results"]]
        return ProxyVec(self.client, Resource, rl)

    def for_object(self, s3obj_spec: S3ObjSpec) -> ProxyVec:
        """Return resources for a given S3 object specification.

        Args:
            s3obj_spec (S3ObjSpec): The S3 object specification.
        Returns:
            ProxyVec: A vector of resources for the given S3 object
        """
        s3url = s3spec_to_url(s3obj_spec)
        return self.search_path(s3url)

    def search(
        self,
        *,
        query: list[str] | None = [],
        order_by: str = None,
        limit: int | None = None,
        offset: int | None = None,
    ):
        """
        Search for resources.

        This is the main function for searching the data catalog for resources.
        Other functions are implemented on top of this one.

        A resource query is a conunction of query terms of the form <field>:<match>.
        The query terms are combined with AND. The match is a string with optional wildcards.


        Arguments:
            query: A list of query strings. Each query string is of the form "<field>:<text>".
            order_by: A field to order by. Only a single field is allowed and only ascending
                     order is supported.
            limit: The maximum number of results to return.
            offset: The offset to start from.

        Returns:
            An answer dict which contains the following fields:
            - count: The number of results found (not the number of results returned).
            - results: A list of dicts, each corresponding to a resource entity.

        """
        search = self.client.api.get_call(Resource, "search")
        query = dict(
            query=query,
            order_by=order_by,
            limit=limit,
            offset=offset,
        )
        return search({k: v for k, v in query.items() if v is not None})
