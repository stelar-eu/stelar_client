from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from .fieldvalidation import AnyField, UUIDField
from .property import Property
from .proxylist import ProxySublist
from .registry import Registry

if TYPE_CHECKING:
    from ..client import Client

Entity = dict[str, Any]


class RefField(AnyField):
    """This field validator is specialized for reference properties"""

    def __init__(self, ref_property: Reference, ref_typename: str, **kwargs):
        super().__init__(**kwargs)
        self.ref_property = ref_property
        self.ref_typename = ref_typename
        self.add_check(self.to_uuid, 5)

    @property
    def proxy_type(self):
        return self.ref_property.proxy_type

    def to_uuid(self, value, **kwargs):
        if not isinstance(value, self.proxy_type):
            raise ValueError(f"Expected {self.proxy_type.__name__}")
        assert isinstance(value.proxy_id, UUID)
        return value.proxy_id, True

    def convert_to_proxy(self, value: str, **kwargs) -> UUID:
        return UUID(value)

    def convert_to_entity(self, value: UUID, **kwargs) -> str:
        return str(value)

    def repr_type(self):
        return self.ref_typename


class Reference(Property):
    """A proxy property which is a reference to an entity."""

    VALIDATOR_CLASS = RefField

    def __init__(
        self,
        proxy_type,
        nullable=False,
        trigger_sync=False,
        **kwargs,
    ):
        val = self.validator_for(proxy_type, nullable=nullable)
        super().__init__(validator=val, **kwargs)
        self.__proxy_type = proxy_type
        self.nullable = nullable
        self.trigger_sync = trigger_sync

    def validator_for(self, proxy_type, **kwargs):
        ptn = self.property_type_name(proxy_type)
        return self.VALIDATOR_CLASS(self, ptn, **kwargs)

    @classmethod
    def property_type_name(cls, proxy_type) -> str:
        if isinstance(proxy_type, str):
            return proxy_type
        else:
            return proxy_type.__name__

    @property
    def proxy_type(self):
        """The class of the proxy object pointed to by this"""
        if isinstance(self.__proxy_type, str):
            from .schema import Schema

            self.__proxy_type = Schema.for_entity(self.__proxy_type).cls
        return self.__proxy_type

    def registry_for(self, obj) -> Registry:
        """Return the registry for the referrent, given owner"""
        return obj.proxy_registry.catalog.registry_for(self.proxy_type)

    def get(self, obj):
        """Low-level getter"""
        if obj.proxy_attr is None:
            obj.proxy_sync()
        if obj.proxy_attr[self.name] is None:
            return None
        else:
            return self.registry_for(obj).fetch_proxy(obj.proxy_attr[self.name])

    def __get__(self, obj, objtype=None):
        val = self.get(obj)

        # The attribute is deleted
        if val is ...:
            raise AttributeError(f"Property '{self.name}' is not present")
        return val

    # set and delete are inherited from Property


class RefListField(AnyField):
    """This field validator is specialized for reference properties"""

    def __init__(
        self,
        ref_property: RefList,
        ref_typename: str,
        *,
        element_validator=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.ref_property = ref_property
        self.ref_typename = ref_typename
        self.element_validator = element_validator
        self.add_check(self.to_list, 5)

    @property
    def proxy_type(self):
        return self.ref_property.proxy_type

    def to_list(self, value, **kwargs):
        if not isinstance(value, list):
            raise ValueError(f"Expected a list")
        if self.element_validator is not None:
            value = [self.element_validator.validate(v) for v in value]
        return value, True

    def convert_to_proxy(self, value: str, **kwargs) -> UUID:
        raise NotImplementedError

    def convert_to_entity(self, value: list, **kwargs) -> str:
        if self.element_validator is not None:
            newval = [self.element_validator.convert_to_entity(v) for v in value]
            return newval

        raise NotImplementedError

    def repr_type(self):
        return self.ref_typename


class RefList(Reference):
    """A proxy property that manages a sub-schema (a sub-collection of other properties)"""

    VALIDATOR_CLASS = RefListField

    def __init__(self, *args, element_validator=UUIDField, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(element_validator, type):
            element_validator = element_validator()
        self.validator.element_validator = element_validator

    @classmethod
    def property_type_name(cls, proxy_type) -> str:
        ptnb = super().property_type_name(proxy_type)
        return f"List[{ptnb}]"

    def get(self, obj):
        """Low-level getter"""
        if obj.proxy_attr is None:
            obj.proxy_sync()
        return obj.proxy_attr[self.name]

    def __get__(self, obj, obj_type=None):
        if obj.proxy_attr is None:
            obj.proxy_sync()
        return ProxySublist(self, obj)

    def set(self, obj, value):
        raise NotImplementedError("Cannot set value of RefList field")

    def convert_entity_to_proxy(self, proxy, entity, **kwargs):
        entities = entity[self.entity_name]
        # entities is a list of entities, we need to fetch them from
        # our proxy's client.
        entity_id_name = self.proxy_type.proxy_schema.id.entity_name
        proxy_ids = [UUID(e.get(entity_id_name)) for e in entities]
        proxy.proxy_attr[self.name] = proxy_ids

    def convert_proxy_to_entity(self, proxy, entity, **kwargs):
        proxy_value = proxy.proxy_attr[self.name]
        if proxy_value is ...:
            return
        entity[self.entity_name] = self.validator.convert_to_entity(
            proxy_value, **kwargs
        )
