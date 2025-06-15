from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from .generic import GenericCursor, GenericProxy
from .proxy import DateField, Id, NameId, Property, Proxy
from .proxy.fieldvalidation import BoolField, LicenseNameField, StrField
from .utils import client_for

if TYPE_CHECKING:
    from . import Client


class License(GenericProxy):
    id = Id()
    key = NameId(validator=LicenseNameField, entity_name="key")
    metadata_created = Property(validator=DateField)
    metadata_modified = Property(validator=DateField)

    title = Property(validator=StrField(nullable=False), updatable=True)
    url = Property(validator=StrField(nullable=True), updatable=True)
    description = Property(validator=StrField(nullable=True), updatable=True)
    image_url = Property(validator=StrField(nullable=True), updatable=True)

    osi_approved = Property(
        validator=BoolField(nullable=False, default=False), updatable=True
    )
    open_data_approved = Property(
        validator=BoolField(nullable=False, default=False), updatable=True
    )


class LicenseCursor(GenericCursor[License]):
    """Cursor for Licenses."""

    def __init__(self, client: Client):
        super().__init__(client, License)


class LicensedProxy(Proxy, entity=False):
    """A proxy that has a license."""

    license_id = Property(validator=StrField(nullable=True), updatable=True)

    @property
    def license(self) -> License | None:
        """Return the License object associated with this proxy, or none."""
        if self.license_id is None:
            return None
        return client_for(self).licenses.get(self.license_id)

    @license.setter
    def license(self, license: License | str | None):
        """Set the license for this proxy."""
        if license is None:
            self.license_id = None
        elif isinstance(license, License):
            self.license_id = license.key
        elif isinstance(license, str):
            self.license_id = license
        elif isinstance(license, UUID):
            self.license_id = str(license)
        else:
            raise TypeError(f"Unsupported type for license: {type(license)}")
