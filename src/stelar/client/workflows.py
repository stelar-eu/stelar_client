from __future__ import annotations

from stelar.client.package import PackageCursor
from stelar.client.proxy.fieldvalidation import UUIDField

from .generic import GenericProxy
from .proxy import (
    DateField,
    ExtrasProperty,
    ExtrasProxy,
    Id,
    NameId,
    Property,
    Reference,
    RefList,
    StateField,
    StrField,
    TaggableProxy,
    TagList,
)
from .resource import Resource
from .utils import client_for


class Workflow(GenericProxy, ExtrasProxy, TaggableProxy):
    id = Id()
    name = NameId()

    metadata_created = Property(validator=DateField)
    metadata_modified = Property(validator=DateField)
    state = Property(validator=StateField)
    type = Property(validator=StrField)
    creator = Property(validator=UUIDField, entity_name="creator_user_id")

    title = Property(validator=StrField, updatable=True)
    notes = Property(validator=StrField(nullable=True), updatable=True)
    author = Property(validator=StrField(nullable=True), updatable=True)
    author_email = Property(validator=StrField(nullable=True), updatable=True)
    maintainer = Property(validator=StrField(nullable=True), updatable=True)
    maintainer_email = Property(validator=StrField(nullable=True), updatable=True)

    # weird ones
    # license_id = Property(validator=StrField(nullable=True), updatable=True)
    url = Property(validator=StrField(nullable=True), updatable=True)
    version = Property(
        validator=StrField(nullable=True, maximum_len=100), updatable=True
    )

    resources = RefList(Resource, trigger_sync=True)
    organization = Reference(
        "Organization",
        entity_name="owner_org",
        create_default="default_organization",
        updatable=True,
        trigger_sync=True,
    )

    groups = RefList("Group", trigger_sync=False)
    extras = ExtrasProperty()
    tags = TagList()


class Task(GenericProxy):
    id = Id()
    start_date = Property(validator=DateField)
    end_date = Property(validator=DateField(nullable=True))

    creator = Property(validator=StrField, entity_name="creator")
    process = Reference("Process", entity_name="process", trigger_sync=True)


class Process(GenericProxy, ExtrasProxy, TaggableProxy):
    """Proxy object for workflow processes (executions)."""

    id = Id()
    name = NameId()

    start_date = Property(validator=DateField)
    end_date = Property(validator=DateField(nullable=True))
    workflow = Reference(
        "Workflow",
        updatable=True,
        nullable=True,
        entity_name="workflow",
        trigger_sync=True,
    )
    tasks = RefList("Task", trigger_sync=True)
    exec_state = Property(validator=StrField)

    metadata_created = Property(validator=DateField)
    metadata_modified = Property(validator=DateField)
    state = Property(validator=StateField)
    type = Property(validator=StrField)
    creator = Property(validator=StrField, entity_name="creator")
    # creator_id = Property(validator=StrField, entity_name="creator")

    title = Property(validator=StrField, updatable=True)
    notes = Property(validator=StrField(nullable=True), updatable=True)
    author = Property(validator=StrField(nullable=True), updatable=True)
    author_email = Property(validator=StrField(nullable=True), updatable=True)
    maintainer = Property(validator=StrField(nullable=True), updatable=True)
    maintainer_email = Property(validator=StrField(nullable=True), updatable=True)

    # weird ones
    url = Property(validator=StrField(nullable=True), updatable=True)
    version = Property(
        validator=StrField(nullable=True, maximum_len=100), updatable=True
    )

    resources = RefList(Resource, trigger_sync=True)
    organization = Reference(
        "Organization",
        entity_name="owner_org",
        create_default="default_organization",
        updatable=True,
        trigger_sync=True,
    )

    groups = RefList("Group", trigger_sync=False)
    extras = ExtrasProperty()
    tags = TagList()

    def add_resource(self, **properties):
        """Add a new resource with the given properties.

        Example:  new_rsrc = d.add_resource(name="Profile", url="s3://datasets/a.json",
            format="json", mimetype="application/json")

        Args:
            **properties: The arguments to pass. See 'Resource' for details.
        """
        return client_for(self).resources.create(dataset=self, **properties)


class ProcessCursor(PackageCursor):
    def __init__(self, client):
        super().__init__(client, Process)
