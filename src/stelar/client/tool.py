from __future__ import annotations

import re
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any

from frozendict import deepfreeze, frozendict

from .api_call import api_call
from .generic import GenericCursor, GenericProxy
from .license import LicensedProxy
from .package import PackageCursor, PackageProxy
from .proxy import (
    AnyField,
    DateFmtField,
    EnumeratedField,
    Id,
    Property,
    StrField,
    derived_property,
)
from .proxy.property import DictProperty
from .task_spec import TaskSpec


class ToolCategoryField(EnumeratedField):
    VALUES = [
        "discovery",
        "interlinking",
        "annotation",
        "other",
    ]


#    {'is_manifest_list': False,                                            │(stelar) vsam@metallurgix:~/git/stelar/stelar_client$ git commit -a
#    'last_modified': 'Sun, 01 Jun 2025 19:45:45 -0000',                             │[main e7923b9] Fixed the proxy resync code related to task creation and termination.
#    'manifest_digest': 'sha256:6e4a55d6531c1aa8844164b552ba7b5f5ef9b30c5d9d94a145777│ 4 files changed, 49 insertions(+), 4 deletions(-)
# c7d26b7c572',                                                                       │(stelar) vsam@metallurgix:~/git/stelar/stelar_client$
#    'name': '0.2.0',                                                                │(stelar) vsam@metallurgix:~/git/stelar/stelar_client$
#    'reversion': False,                                                             │(stelar) vsam@metallurgix:~/git/stelar/stelar_client$ git pull
#    'size': 56837148,                                                               │Already up to date.
#    'start_ts': 1748807145
# }


@dataclass
class Image:
    """A container image used by a tool.

    Images are just information objects, they are not proxies.
    """

    is_manifest_list: bool
    last_modified: datetime
    manifest_digest: str
    tool: Tool  # The tool this image belongs to
    name: str
    reversion: bool
    size: int
    start_ts: datetime

    def __post_init__(self):
        if isinstance(self.last_modified, str):
            self.last_modified = datetime.strptime(
                self.last_modified, "%a, %d %b %Y %H:%M:%S -0000"
            )
        if isinstance(self.start_ts, int):
            self.start_ts = datetime.fromtimestamp(self.start_ts)

    @property
    def id(self):
        """Return a unique identifier for this image."""
        return f"stelar/{self.tool.name}:{self.name}"

    def __repr__(self):
        return f"Image({self.tool.name}/{self.name})"


IMAGE_TAG_PATTERN = re.compile(r"[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}$")
KUBERNETES_NAME_PATTERN = re.compile(r"[a-z0-9]([-a-z0-9]*[a-z0-9])?")
CPU_QUANTITY_PATTERN = re.compile(r"^\d+(\.\d+)?[m]?$")
MEMORY_QUANTITY_PATTERN = re.compile(r"^\d+(\.\d+)?(Ki|Mi|Gi|Ti|Pi|Ei|k|M|G|T|P|E)?$")
RESTART_POLICY_VALUES = ["Always", "OnFailure", "Never"]
IMAGE_PULL_POLICY_VALUES = ["Always", "IfNotPresent", "Never"]


@dataclass(frozen=True)
class ToolProfile:
    """An object specifying options for executing images of a tool."""

    image: str | None = None
    """The image to use for this tool, if specified."""
    description: str | None = None
    image_pull_policy: str | None = None
    image_pull_secrets: list[str] | None = None
    cpu_request: str | None = None
    cpu_limit: str | None = None
    memory_request: str | None = None
    memory_limit: str | None = None
    backoff_limit: int | None = None
    restart_policy: str | None = None
    ttl_seconds_after_finished: int | None = None

    def __post_init__(self):
        self.validate_image(self.image)
        self.validate_image_pull_policy(self.image_pull_policy)
        self.validate_image_pull_secrets(self.image_pull_secrets)
        self.validate_cpu_request(self.cpu_request)
        self.validate_cpu_limit(self.cpu_limit)
        self.validate_memory_request(self.memory_request)
        self.validate_memory_limit(self.memory_limit)
        self.validate_backoff_limit(self.backoff_limit)
        self.validate_restart_policy(self.restart_policy)
        self.validate_ttl_seconds_after_finished(self.ttl_seconds_after_finished)

    @staticmethod
    def validate(attr_name: str, value: Any):
        """Validate a single attribute of the tool profile."""
        validator = getattr(ToolProfile, f"validate_{attr_name}", None)
        if validator is None:
            raise ValueError(f"Invalid attribute: {attr_name}")
        return validator(value)

    @staticmethod
    def validate_image(image) -> None:
        if image is not None and not IMAGE_TAG_PATTERN.fullmatch(image):
            raise ValueError(
                f"Invalid image name: {image}. Must match {IMAGE_TAG_PATTERN.pattern}"
            )

    @staticmethod
    def validate_image_pull_policy(policy: str | None) -> None:
        if policy is not None and policy not in IMAGE_PULL_POLICY_VALUES:
            raise ValueError(
                f"Invalid image pull policy: {policy}. Must be one of {IMAGE_PULL_POLICY_VALUES}."
            )

    @staticmethod
    def validate_image_pull_secrets(secrets: list[str] | None) -> None:
        if secrets is not None:
            if not isinstance(secrets, list | tuple):
                raise TypeError(
                    f"Image pull secrets must be a list or tuple, got {type(secrets)}"
                )
            if not all(KUBERNETES_NAME_PATTERN.fullmatch(secret) for secret in secrets):
                raise ValueError(
                    f"Invalid image pull secret names: {secrets}. Must match {KUBERNETES_NAME_PATTERN.pattern}"
                )

    @staticmethod
    def validate_cpu_request(cpu_request: str | None) -> None:
        if cpu_request is not None and not CPU_QUANTITY_PATTERN.fullmatch(cpu_request):
            raise ValueError(
                f"Invalid CPU request: {cpu_request}. Must match {CPU_QUANTITY_PATTERN.pattern}"
            )

    @staticmethod
    def validate_cpu_limit(cpu_limit: str | None) -> None:
        if cpu_limit is not None and not CPU_QUANTITY_PATTERN.fullmatch(cpu_limit):
            raise ValueError(
                f"Invalid CPU limit: {cpu_limit}. Must match {CPU_QUANTITY_PATTERN.pattern}"
            )

    @staticmethod
    def validate_memory_request(memory_request: str | None) -> None:
        if memory_request is not None and not MEMORY_QUANTITY_PATTERN.fullmatch(
            memory_request
        ):
            raise ValueError(
                f"Invalid memory request: {memory_request}. Must match {MEMORY_QUANTITY_PATTERN.pattern}"
            )

    @staticmethod
    def validate_memory_limit(memory_limit: str | None) -> None:
        if memory_limit is not None and not MEMORY_QUANTITY_PATTERN.fullmatch(
            memory_limit
        ):
            raise ValueError(
                f"Invalid memory limit: {memory_limit}. Must match {MEMORY_QUANTITY_PATTERN.pattern}"
            )

    @staticmethod
    def validate_backoff_limit(backoff_limit: int | None) -> None:
        if backoff_limit is not None and (
            not isinstance(backoff_limit, int) or backoff_limit < 0
        ):
            raise ValueError(
                f"Invalid backoff limit: {backoff_limit}. Must be a non-negative integer."
            )

    @staticmethod
    def validate_restart_policy(restart_policy: str | None) -> None:
        if restart_policy is not None and restart_policy not in RESTART_POLICY_VALUES:
            raise ValueError(
                f"Invalid restart policy: {restart_policy}. Must be one of {RESTART_POLICY_VALUES}."
            )

    @staticmethod
    def validate_ttl_seconds_after_finished(ttl_seconds: int | None) -> None:
        if ttl_seconds is not None and (
            not isinstance(ttl_seconds, int) or ttl_seconds < 0
        ):
            raise ValueError(
                f"Invalid TTL seconds after finished: {ttl_seconds}. Must be a non-negative integer."
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert the tool profile to a dictionary, omit None values."""
        return {
            field.name: getattr(self, field.name)
            for field in fields(self)
            if getattr(self, field.name) is not None
        }


class ProfilesField(AnyField):
    """A field for storing tool profiles as a dictionary."""

    def __init__(self, **kwargs):
        super().__init__(nullable=False, **kwargs)
        self.add_check(self.to_frozendict, 5)

    def to_frozendict(
        self, value: dict[str, ToolProfile | dict], **kwargs
    ) -> tuple[frozendict, bool]:
        """Convert a dictionary of ToolProfile objects to a frozendict."""
        if not isinstance(value, (dict, frozendict)):
            raise TypeError(f"Expected dict, got {type(value)}")

        fprof = {}
        for key, profile in value.items():
            if not isinstance(profile, (ToolProfile | dict | frozendict)):
                raise TypeError(
                    f"Expected profile dict or ToolProfile, got {type(profile)}"
                )
            try:
                ToolProfile.validate_image(key)
            except Exception as e:
                raise ValueError(f"Invalid profile name '{key}': {e}")
            if isinstance(profile, dict | frozendict):
                try:
                    ToolProfile(**profile)
                except Exception as e:
                    raise ValueError(f"Invalid profile data for '{key}': {e}")
                fprof[key] = profile
            else:
                fprof[key] = profile.to_dict()
        return deepfreeze(fprof), False

    def convert_to_proxy(self, value: Any, **kwargs) -> frozendict:
        return deepfreeze(value)


class Tool(PackageProxy, LicensedProxy):
    # weird ones
    # license_id = Property(validator=StrField(nullable=True), updatable=True)
    git_repository = Property(validator=StrField(nullable=True), updatable=True)
    programming_language = Property(validator=StrField(nullable=True), updatable=True)
    version = Property(
        validator=StrField(nullable=True, maximum_len=100), updatable=True
    )

    inputs = DictProperty(str, str, updatable=True)
    outputs = DictProperty(str, str, updatable=True)
    parameters = DictProperty(str, str, updatable=True)
    category = Property(validator=ToolCategoryField(nullable=True), updatable=True)
    repository = Property(validator=StrField(nullable=False), updatable=False)

    profiles = Property(validator=ProfilesField, updatable=True)

    def get_profile(self, name="default", default=None) -> ToolProfile | None:
        """Return the tool profile for the given name."""
        if name not in self.profiles:
            return default
        return ToolProfile(**self.profiles[name])

    def set_profile(
        self, name: str, profile: ToolProfile | dict | None = None, **pargs
    ) -> None:
        ps = self.profiles
        if profile is None:
            profile = ToolProfile(**pargs)
        elif isinstance(profile, dict):
            profile = ToolProfile(**(profile | pargs))

        self.profiles = ps.set(name, profile)

    def update_profile(self, name: str, **pargs) -> None:
        """Update the tool profile with the given name."""
        ps = self.profiles
        prof = ps.get(name, {})

        prof |= pargs
        return self.set_profile(name, prof)

    def delete_profile(self, name: str) -> None:
        """Delete the tool profile with the given name."""
        ps = dict(self.profiles)
        if name in ps:
            del ps[name]
            self.profiles = ps

    @derived_property
    def images(self, entity):
        """Return a list of images associated with this tool."""
        images = entity.get("images", [])
        return [Image(tool=self, **image) for image in images]

    def get_image(self, name: str | None = None, default=None) -> Image | None:
        """Return the image of the given name, or the default image

        for this tool, if any.
        """
        if name is not None:
            for image in self.images:
                if image.name == name:
                    return image
            return default

        # No name, return the default image if it exists
        dprof = self.get_profile()
        if dprof and dprof.image:
            # If a default profile is set, return the image from that profile
            return self.get_image(dprof.image, default)
        img = self.images
        if len(img) == 1:
            # If there's only one image, return it
            return img[0]
        return None

    def task_spec(self, profile_or_image=None):
        """Return a new TaskSpec initialized for this tool.

        Args
            profile_or_image: Either a profile name or an image name.
                If a profile name is given, the image from that profile
                will be used. If an image name is given, it will be used
                directly.
        """
        # if image not in self.profiles
        return TaskSpec(tool=self, image=profile_or_image)


class ToolCursor(PackageCursor[Tool]):
    def __init__(self, client):
        super().__init__(client, Tool)


class ImageRegistryToken(GenericProxy):
    """A token representing an image used by a tool."""

    DATEFORMAT = "%a, %d %b %Y %H:%M:%S %z"

    id = Id(entity_name="uuid")
    created = Property(validator=DateFmtField(DATEFORMAT), updatable=False)
    expiration = Property(
        validator=DateFmtField(DATEFORMAT, nullable=True), updatable=False
    )
    last_accessed = Property(
        validator=DateFmtField(DATEFORMAT, nullable=True), updatable=False
    )

    title = Property(validator=StrField(nullable=False), updatable=False)

    token = Property(
        validator=StrField(nullable=False), updatable=False, entity_name="token_code"
    )


class ImageRegistryTokenCursor(GenericCursor[ImageRegistryToken]):
    """A cursor for iterating over image registry tokens."""

    def __init__(self, client):
        super().__init__(client, ImageRegistryToken)

    def create(
        self, title: str, expiration: datetime | None = None
    ) -> ImageRegistryToken:
        """Create a new image registry token."""
        ac = api_call(self)
        result = ac.image_registry_token_create(title=title, expiration=expiration)
        return self.fetch_proxy_for_entity(result)
