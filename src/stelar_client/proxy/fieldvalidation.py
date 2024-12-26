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
from typing import Optional, TYPE_CHECKING, TypeVar, Generic, Any
from uuid import UUID
from datetime import datetime


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

    def __init__(self, *, 
                 strict: bool=False, 
                 nullable: bool = True, 
                 minimum_value: Any = None, maximum_value: Any = None,
                 maximum_len: Optional[int]=None, minimum_len: Optional[int]=None):
        
        self.prioritized_checks = []
        self.checks = []
        self.strict = strict
        self.nullable = nullable
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
        self.prioritized_checks.sort(key= lambda p: p[1])
        self.checks = [p[0] for p in self.prioritized_checks]

    def check_null(self, value):
        if value is None:
            if self.nullable:
                return None, True
            else:
                raise ValueError("None is not allowed")
        else:
            return value, False
        
    def check_length(self, value):
        value_len = len(value)
        if self.minimum_len is not None and value_len < self.minimum_len:
            raise ValueError(f"The length ({value_len}) is less than the minimum ({self.minimum_len})")
        if self.maximum_len is not None and value_len > self.maximum_len:
            raise ValueError(f"The length ({value_len}) is greater that the maximum ({self.maximum_len})")
        return value, False

    def check_minimum(self, value):
        if value < self.minimum_value:
            raise ValueError(f"Value ({value}) too low (minimum={self.minimum_value})")
        return value, False

    def check_maximum(self, value):
        if value > self.maximum_value:
            raise ValueError(f"Value ({value}) too high (maximum={self.maximum_value})")
        return value, False

    def validate(self, value):
        done = False
        try:
            for check in self.checks:
                value, done = check(value)
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
        
    def convert_to_proxy(self, value):
        raise NotImplementedError()
    def convert_to_entity(self, value):
        raise NotImplementedError()


class AnyField(FieldValidator):
    """A very promiscuous basic validator."""
    def convert_to_proxy(self, value):
        return value
    def convert_to_entity(self, value):
        return value


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

    def to_ftype(self, value):
        if not isinstance(value, self.ftype):
            value = self.ftype(value)
        return value, False


class StrField(BasicField):
    """A string field validator"""
    def __init__(self, **kwargs):
        super().__init__(ftype=str, **kwargs)


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

    def to_date(self, value: Any) -> tuple[datetime, bool]:
        if isinstance(value, str):
            return datetime.fromisoformat(value), False
        elif isinstance(value, datetime):
            return value, False
        else:
            raise ValueError("Invalid type, expected datetime or string")

    def convert_to_entity(self, value: datetime) -> str:
        return value.isoformat()
    def convert_to_proxy(self, value: str) -> datetime:
        return datetime.fromisoformat(value)


class UUIDField(BasicField):
    def __init__(self, **kwargs):
        super().__init__(ftype=UUID, **kwargs)
    def convert_to_proxy(self, value: str) -> UUID:
        return UUID(value)
    def convert_to_entity(self, value: UUID) -> str:
        return str(value)