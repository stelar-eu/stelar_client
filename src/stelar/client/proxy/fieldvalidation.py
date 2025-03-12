"""
Proxy field validation
----------------------

Proxied entity fields (attributes) have two representations: one
that appears in the entity (JSON object stored in a dict) and one that is used
by the proxy objects.

client proxy value  <-->  json entity value

For example, dates are represented as datetime objects in the proxy and as strings
in the JSON entity. Conversion between the two is done via the two conversion methods
of the classes herein.
"""

from __future__ import annotations

import re
from collections.abc import MutableSequence
from datetime import datetime
from typing import Any, Mapping, Optional
from uuid import UUID

__all__ = [
    "FieldValidator",
    "AnyField",
    "EnumeratedField",
    "StateField",
    "BoolField",
    "IntField",
    "StrField",
    "DateField",
    "UUIDField",
    "NameField",
    "TagNameField",
    "VocabNameField",
]


class FieldValidator:
    """Provide simple validation and conversion for entity fields.

        A validation is a sequence of checks. Each check can:
        - Raise an exception of ValueError
        - Apply a value conversion and continue
        - Apply a value conversion and terminate

    Any function that takes as input a value, and returns a pair (newvalue, done)
    where `done` is a boolean, can be used as a check.

    At the end of all conversions, if no conversion signaled `done`, the `strict` attribute
    is checked. If True, an error is raised, else (the default) conversion succeeds.
    """

    def __init__(
        self,
        *,
        strict: bool = False,
        nullable: bool = True,
        default: Any = ...,
        minimum_value: Any = None,
        maximum_value: Any = None,
        maximum_len: Optional[int] = None,
        minimum_len: Optional[int] = None,
    ):
        self.prioritized_checks = []
        self.checks = []
        self.strict = strict
        self.nullable = nullable
        if default is not ...:
            self.default = default
        self.minimum_value = minimum_value
        self.maximum_value = maximum_value
        self.maximum_len = maximum_len
        self.minimum_len = minimum_len

        if nullable is not None:
            self.add_check(self.check_null, -1)

        if minimum_value is not None:
            self.add_check(self.check_minimum, 10)
        if maximum_value is not None:
            self.add_check(self.check_maximum, 12)
        if maximum_len is not None or minimum_len is not None:
            self.add_check(self.check_length, 20)

    def add_check(self, check_func, pri: int):
        self.prioritized_checks.append((check_func, pri))
        self.prioritized_checks.sort(key=lambda p: p[1])
        self.checks = [p[0] for p in self.prioritized_checks]

    def check_null(self, value, **kwargs):
        if value is None:
            if self.nullable:
                return None, True
            else:
                raise ValueError("None is not allowed")
        else:
            return value, False

    def check_length(self, value, **kwargs):
        value_len = len(value)
        if self.minimum_len is not None and value_len < self.minimum_len:
            raise ValueError(
                f"The length ({value_len}) is less than the minimum ({self.minimum_len})"
            )
        if self.maximum_len is not None and value_len > self.maximum_len:
            raise ValueError(
                f"The length ({value_len}) is greater that the maximum ({self.maximum_len})"
            )
        return value, False

    def check_minimum(self, value, **kwargs):
        if value < self.minimum_value:
            raise ValueError(f"Value ({value}) too low (minimum={self.minimum_value})")
        return value, False

    def check_maximum(self, value, **kwargs):
        if value > self.maximum_value:
            raise ValueError(f"Value ({value}) too high (maximum={self.maximum_value})")
        return value, False

    def validate(self, value, **kwargs):
        done = False
        try:
            for check in self.checks:
                value, done = check(value, **kwargs)
                if done:
                    return value
        except ValueError:
            raise
        except Exception as e:
            raise ValueError("Bad value found during validation") from e

        if self.strict:
            raise ValueError("Validation failed to match input value")
        else:
            return value

    def convert_to_proxy(self, value, **kwargs):
        raise NotImplementedError()

    def convert_to_entity(self, value, **kwargs):
        raise NotImplementedError()

    def default_value(self):
        raise NotImplementedError

    def repr_constraints(self):
        nn = ["nullable" if self.nullable else "not null"]

        if self.minimum_len is not None and self.maximum_len is not None:
            nn.append(f"{self.minimum_len} <= length <= {self.maximum_len}")
        elif self.minimum_len is not None:
            nn.append(f"{self.minimum_len} <= length")
        elif self.maximum_len is not None:
            nn.append(f"length <= {self.maximum_len}")

        if self.minimum_value is not None and self.maximum_value is not None:
            nn.append(f"{self.minimum_value} <= value <={self.maximum_value}")
        elif self.minimum_value is not None:
            nn.append(f"{self.minimum_value} <= value")
        elif self.maximum_value is not None:
            nn.append(f"value <= {self.maximum_value}")

        return nn


class AnyField(FieldValidator):
    """A very promiscuous basic validator."""

    def __init__(self, repr_type="Any", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._repr_type = repr_type

    def convert_to_proxy(self, value, **kwargs):
        return value

    def convert_to_entity(self, value, **kwargs):
        return value

    def default_value(self):
        if hasattr(self, "default"):
            return self.default
        elif self.nullable:
            return None
        else:
            raise NotImplementedError()

    def repr_type(self):
        return self._repr_type


class EnumeratedField(AnyField):
    """Fields with a fixed set of legal values.

    Subclasses can redefine the VALUES class attribute.
    """

    VALUES = []

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.add_check(self.oneof, 5)

    def oneof(self, value):
        if value not in self.VALUES:
            raise ValueError(f"Not one of {self.VALUES}")
        return value, False

    def repr_type(self):
        return f"OneOf{self.VALUES}"


class StateField(EnumeratedField):
    VALUES = ["active", "deleted"]

    def __init__(self):
        super().__init__(nullable=False)


class ExecStateField(EnumeratedField):
    VALUES = ["running", "succeeded", "failed"]

    def __init__(self):
        super().__init__(nullable=False)


class BasicField(AnyField):
    """
    Given ftype T, accept value if it is an instance of T or if T(value) succeeds.
    Conversion to T is performed.

    Subclasses include basic types: str, int, bool
    """

    def __init__(self, ftype, **kwargs):
        super().__init__(**kwargs)
        self.ftype = ftype
        self.add_check(self.to_ftype, 5)

    def to_ftype(self, value, **kwargs):
        """Validator stage for BasicField"""
        if not isinstance(value, self.ftype):
            value = self.ftype(value)
        return value, False

    def repr_type(self):
        return self.ftype.__name__


class StrField(BasicField):
    """A string field validator"""

    def __init__(self, **kwargs):
        super().__init__(ftype=str, **kwargs)


class NameField(StrField):
    """Name fields are non-nullable string fields whose value
    must follow a pattern.
    """

    def __init__(self, **kwargs):
        super().__init__(nullable=False, minimum_len=2, maximum_len=100, **kwargs)
        self.add_check(self.check_name, 7)

    NAME_PATTERN = re.compile(r"[a-z0-9_-]+")

    def check_name(self, value: str, **kwargs):
        if self.NAME_PATTERN.fullmatch(value) is None:
            raise ValueError(
                f"Name must be a string matching '{self.NAME_PATTERN.pattern}'"
            )
        return value, False


class VocabNameField(NameField):
    NAME_PATTERN = re.compile(r".+")


class TagNameField(NameField):
    NAME_PATTERN = re.compile(r"[A-Za-z0-9 ._-]+")


class IntField(BasicField):
    """An int field validator"""

    def __init__(self, **kwargs):
        super().__init__(ftype=int, **kwargs)


class BoolField(BasicField):
    """A bool field validator"""

    def __init__(self, **kwargs):
        super().__init__(ftype=bool, **kwargs)


class DateField(FieldValidator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_check(self.to_date, 5)

    def to_date(self, value: Any, **kwargs) -> tuple[datetime, bool]:
        """Validation stage for dates."""
        if isinstance(value, str):
            return datetime.fromisoformat(value), False
        elif isinstance(value, datetime):
            return value, False
        else:
            raise ValueError("Invalid type, expected datetime or string")

    def convert_to_entity(self, value: datetime, **kwargs) -> str:
        return value.isoformat()

    def convert_to_proxy(self, value: str, **kwargs) -> datetime:
        return datetime.fromisoformat(value)

    def repr_type(self):
        return "datetime"


class DictField(AnyField):
    def __init__(self, key_type, value_type, **kwargs):
        super().__init__(**kwargs)
        self.key_type = key_type
        self.value_type = value_type
        self._repr_type = f"Dict[{key_type},{value_type}]"
        self.add_check(self.check_dict, 5)

    def check_dict(self, value, **kwargs):
        if not isinstance(value, Mapping):
            raise TypeError("Expected a dictionary")
        for k, v in value.items():
            if not isinstance(k, self.key_type):
                raise TypeError(f"Invalid key type, expected {self.key_type}")
            if not isinstance(v, self.value_type):
                raise TypeError(f"Invalid value type, expected {self.value_type}")
        return dict(value), False


class ListField(AnyField):
    def __init__(self, element_type, **kwargs):
        super().__init__(**kwargs)
        self.element_type = element_type
        self._repr_type = f"List[{element_type}]"
        self.add_check(self.check_list, 5)

    def check_list(self, value, **kwargs):
        if not isinstance(value, MutableSequence):
            raise TypeError("Expected a list")
        for v in value:
            if not isinstance(v, self.element_type):
                raise TypeError(f"Invalid element type, expected {self.element_type}")
        return list(value), False

    def repr_type(self):
        return self._repr_type


class UUIDField(BasicField):
    def __init__(self, **kwargs):
        super().__init__(ftype=UUID, **kwargs)

    def convert_to_proxy(self, value: str, **kwargs) -> UUID:
        try:
            return UUID(value)
        except ValueError:
            raise ValueError("Invalid UUID", value, kwargs)

    def convert_to_entity(self, value: UUID, **kwargs) -> str:
        return str(value)

    def repr_type(self):
        return "UUID"
