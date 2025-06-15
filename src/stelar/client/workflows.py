from __future__ import annotations

from .license import LicensedProxy
from .package import PackageProxy
from .proxy import Property, StrField


class Workflow(PackageProxy, LicensedProxy):
    title = Property(validator=StrField, updatable=True)
    version = Property(
        validator=StrField(nullable=True, maximum_len=100), updatable=True
    )

    repository = Property(validator=StrField(nullable=True), updatable=True)
    executor = Property(validator=StrField(nullable=True), updatable=True)
