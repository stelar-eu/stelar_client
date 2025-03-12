"""Declare utilities for package-derived types of entities.

These will be:
- datasets
- workflows
- workflow processes
- tools
"""

from typing import Any, TypeVar
from uuid import UUID

from .generic import GenericCursor
from .named import NamedProxy
from .proxy import (
    BoolField,
    DateField,
    Property,
    ProxyVec,
    Reference,
    RefList,
    StrField,
    TaggableProxy,
    TagList,
    UUIDField,
)
from .utils import tag_split
from .vocab import Tag


class PackageProxy(NamedProxy, TaggableProxy, entity=False):
    # Auto-maintained fields
    metadata_created = Property(validator=DateField)
    metadata_modified = Property(validator=DateField)

    creator = Property(validator=UUIDField, entity_name="creator_user_id")
    private = Property(
        validator=BoolField(nullable=False, default=False), updatable=True
    )

    organization = Reference(
        "Organization",
        entity_name="owner_org",
        create_default="default_organization",
        updatable=True,
        trigger_sync=True,
    )

    tags = TagList()
    groups = RefList("Group", trigger_sync=False)

    # User-maintained fields
    notes = Property(validator=StrField(nullable=True), updatable=True)
    author = Property(validator=StrField(nullable=True), updatable=True)
    author_email = Property(validator=StrField(nullable=True), updatable=True)
    maintainer = Property(validator=StrField(nullable=True), updatable=True)
    maintainer_email = Property(validator=StrField(nullable=True), updatable=True)


PackageProxyType = TypeVar("PackageProxy", bound=PackageProxy)


class PackageCursor(GenericCursor[PackageProxyType]):
    def __init__(self, client, proxy_type):
        super().__init__(client, proxy_type)

    def search(
        self,
        *,
        q: str | None = None,
        bbox: list[float] | None = None,
        fq: list[str] = [],
        fl: list[str] = None,
        sort: str = None,
        limit: int | None = None,
        offset: int | None = None,
        facet: dict[str, Any] | None = None,
    ):
        """
        Search for package-based entities (datasets, tools, workflows etc).

        This is the main function for searching the data catalog for packages.
        Many other functions are implemented on top of this one.

        Arguments:
            q: The query string.
            bbox: A list of four floats representing the bounding box of a spatial query.
            fq: A list of filter queries. These are not used to obtain the score of the results,
               but instead just to filter the results. They are quite efficient.
            fl: A list of fields to return. If None, a proper entity is returned.
                Note that some fields are special (not actually attribute fields), e.g.,
                the score field.
            sort: The fields to sort by. Sorting can be ascending or descending.
            limit: The maximum number of results to return.
            offset: The offset to start from.
            facet: A dictionary of facet field spec (facet attributes and limits).

        Returns:
            An answer which contains the following fields:
            - count: The number of results found (not the number of results returned).
            - results: A list of results.
            - facets: A dictionary of facets.

        """
        search = self.client.api.get_call(self.proxy_type, "search")
        args = dict(
            q=q,
            bbox=bbox,
            fq=fq,
            fl=fl,
            sort=sort,
            limit=limit,
            offset=offset,
            facet=facet,
        )
        query = {k: v for k, v in args.items() if v is not None}
        return search(query)

    def with_tag(
        self, tagarg: Tag | str, *, limit: int | None = None, offset: int | None = None
    ):
        """Return a list of entities ids which have the given tag

        Arguments:
            tagarg: A Tag (proxy) or tagspec (a string)
            limit: The maximum number of results to return.
            offset: The offset to start from.

        Returns:
            A proxy list of entity ids
        """
        # Need to obtain the tag ID, in order to call tag_show
        if isinstance(tagarg, Tag):
            return self.with_tag(tagarg.tagspec, limit=limit, offset=offset)

        # Assume that tagarg is a string
        voc, tag = tag_split(tagarg)

        if voc is None:
            filter = f'tags:"{tag}"'
        else:
            filter = f'vocab_{voc}:"{tag}"'

        rids = self.search(fq=[filter], fl=["id"], limit=limit, offset=offset)
        ids = [UUID(r["id"]) for r in rids["results"]]
        return ProxyVec(self.client, self.proxy_type, ids)
