from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from .decl import ProxyState
from .exceptions import ConversionError, ErrorState, InvalidationError

if TYPE_CHECKING:
    from pandas import Series

    from .registry import Registry, RegistryCatalog

"""
    Introduction
    ------------

    Proxy objects represent STELAR entities in Python:
    - Datasets
    - Resources
    - Workflows
    - Groups
    - Organizations
    - Processes (workflow executions)
    - Tasks
    - Tools
    - Policies
    - Users

    They can be used to
    - inspect
    - update
    - delete
    - link and relate
    - plus, custom operations

    The proxy object base class implements generic handling of properties:
    - initializing properties
    - loading propertties on demand
    - updating single properties
    - updating multiple properties

"""


# ----------------------------------------------------------
#
# Proxy is the base class for all proxy classes
#
# ----------------------------------------------------------

Entity = dict[str, Any]


class Proxy:
    """Base class for all proxy objects of the STELAR entities.

    Proxy objects are managed by Registry. The primary implementation
    of Registry is Client.

    A proxy can be in one of four states:
      - ``EMPTY``: there is no entity data in the proxy
      - ``CLEAN``: the data loaded by the last proxy_sync() operation is not changed
      - ``DIRTY``: the data loaded by the last proxy_sync() operation has been changed
      - ``ERROR``: the proxy is illegal! This state can be the result of deleting entity


    Attributes are used to hold property values:

    proxy_registry:
        The Registry instance that this proxy belongs to

    proxy_id:
        The UUID of the proxies entity

    proxy_attr:
        A dict of all loaded attributes. When None, the entity has
        not yet been loaded. The state is EMPTY

    proxy_changed:
        A dict of all changed attributes (loaded values of updated attributes)
        since last upload. When None, the entity is ``CLEAN`` (or ``EMPTY``), else the
        entity is ``DIRTY``.

    To initialize a proxy object, one must supply either an entity id or
    an entity JSON body. The proxy_id is never changed. When an entity is deleted,
    set the proxy_id to None, to mark the proxy state as ``ERROR``.

    After initialization, the state of a proxy is ``EMPTY``.

    Proxies are handlers for **entities** of the Stelar Service API. Entities are manipulated
    by a CRUD-like API. Besides creation and deletion, entities are manipulated by two additional
    I/O API operations:
    - fetch, which returns an entity data from the API
    - update, which accepts a spec of the updates to apply to an entity. This operation often returns
    the updated object after updates are applied.

    The following operations operate on proxies:

    proxy_sync(entity=None):
        Save any pending updates to make the state CLEAN. Load the proxy data
        from the Stelar Service API, to make sure the proxy has the latest. When `entity` is not None,
        use it to avoid a fetch.

    proxy_invalidate(force=False):
        Make the object EMPTY. If the proxy is DIRTY, an IvalidationError
        is raised, unless `force` is specified as True.

    proxy_reset():
        Make a DIRTY object to CLEAN, by restoring the property values of the last sync().

    proxy_sync(entity=None):
        Make an entity CLEAN.
    """

    proxy_registry: Registry
    proxy_id: Optional[UUID]
    proxy_autosync: bool
    proxy_attr: dict[str, Any] | None
    proxy_changed: dict[str, Any] | None

    def __init__(
        self, registry: Registry, eid: Optional[str | UUID] = None, entity=None
    ):
        self.proxy_registry = registry
        self.proxy_autosync = True

        if eid is None and entity is None:
            raise ValueError(
                "A proxy must be initialized either with an entity ID"
                " or with an entity JSON object containing the ID"
            )

        if entity is not None:
            if eid is None:
                try:
                    eid = entity[self.proxy_schema.id.entity_name]
                except KeyError as e:
                    raise ValueError(
                        "A proxy must be initialized either with an entity ID"
                        " or with an entity JSON object containing the ID"
                    ) from e
            # this is a check which is not really necessary...
            elif self.proxy_schema.id.entity_name in entity:
                if str(eid) != str(entity[self.proxy_schema.id.entity_name]):
                    raise ValueError(
                        "Mismatch between entity ID provided directly and indirectly"
                    )

        if not isinstance(eid, UUID):
            self.proxy_id = UUID(eid)
        else:
            self.proxy_id = eid

        self.proxy_attr = None
        self.proxy_changed = None

    def __init_subclass__(cls, entity=True):
        from .schema import Schema

        if entity:
            cls.proxy_schema = Schema(cls)
        else:
            # cls is not an entity class, check it
            Schema.check_non_entity(cls)

    @classmethod
    def new(
        cls, regspec: Registry | RegistryCatalog, *, autosync: bool = True, **fields
    ):
        """Return a non-affiliated proxy instance, i.e. a 'creation proxy'.

        This proxy instance's id is UUID(int=0), which is indicative
        of a non-valid id. The purpose of such an object is to
        create a new entity, by calling 'proxy_sync()'.

        While the UUID is 0, this entity is not registered in
        the registry. Therefore, multiple such entries can exist.
        However, once the entity is proxy_sync'd, its id changes
        to a proper one and the object is registered in the
        registry.

        Args:
            cls (Type[ProxyClass]): the proxy type for the new proxy.

            regspec (Registry|RegistryCatalog): Registry spec for the new object.
               If regspec is a Registry, its catalog is used to locate a suitable registry
               for the 'cls' proxy type, via regspec.catalog.registry_for(cls).
               If regspec is a catalog, it provides the registry via regspec.registry_for(cls).

            autosync (bool, default: True): When True, the new entity is created (by calling
                proxy_sync() on the proxy) before returning. When False, the new entity
                is not yet created, a call to proxy_sync() must be done later.

                Note that the proxy_aytosync field of the returned proxy is set to true, regardless
                of the value of this parameter.

            fields (dict[str][Any]):  values to initialize the new entity from

        Returns:
            A proxy to a new entity. If autosync if False, the new proxy does not yet correspond
            to an entity.
        """
        from .registry import Registry, RegistryCatalog

        if not hasattr(cls, "proxy_schema"):
            raise TypeError(f"Class {cls.__name__} is not an entity class")

        if isinstance(regspec, RegistryCatalog):
            registry = regspec.registry_for(cls)
        elif isinstance(regspec, Registry):
            registry = regspec.catalog.registry_for(cls)
        else:
            raise TypeError("Expected Registry or RegistryCatalog for regspec")

        schema = cls.proxy_schema
        proxy = cls(registry, eid=UUID(int=0))

        # Validate the given fields
        validated_fields = {
            name: schema.properties[name].validator.validate(value)
            for name, value in fields.items()
            if name in schema.all_fields
        }

        # For the missing fields, add the default, or ...
        # Adding ..., implies somehow that the field has been deleted (!)
        for name, prop in schema.properties.items():
            if not (prop.isId or prop.isExtras or name in validated_fields):
                defval = prop.missing(proxy=proxy)
                if defval is ...:
                    validated_fields[name] = ...
                else:
                    try:
                        validated_fields[name] = prop.validate(proxy, defval)
                    except ValueError as e:
                        raise ConversionError(prop, "validate") from e
                # if False:  # prop.create_default is not None:
                #    validated_fields[name] = prop.create_default
                # else:
                #    validated_fields[name] = ...

        # Finally, if we have extras, use extras field for any unrecognized
        # items in fields
        if schema.extras is not None:
            validated_fields[schema.extras.name] = {
                ename: schema.extras.item_validator.validate(evalue)
                for ename, evalue in fields.items()
                if ename not in validated_fields
            }

        # Set up the dictionaries of the proxy
        proxy.proxy_attr = validated_fields
        proxy.proxy_changed = dict()

        if autosync:
            proxy.proxy_sync()
        return proxy

    @classmethod
    def new_entity(cls, catalog: RegistryCatalog = None, /, **fields) -> Entity:
        """Return a set of fields for creating a new entity.

        Args
        ----
            fields: dict[str,Any]
        """
        if not hasattr(cls, "proxy_schema"):
            raise TypeError(f"Class {cls.__name__} is not an entity class")
        entity_fields = {}
        for property in cls.proxy_schema.properties.values():
            property.convert_to_create(
                cls,
                fields,
                entity_fields,
                catalog=catalog,
                registry=catalog.registry_for(cls) if catalog else None,
            )
        return entity_fields

    def delete(self, purge: bool = False):
        """Delete the entity and mark the proxy as invalid.
        Entity classes can overload this method, to perform the
        actual API delete. When successful, they can then
        invoke Proxy.delete() to mark this proxy as invalid.
        """
        if self.proxy_state is ProxyState.ERROR:
            return  # Not an error to call delete on purged entity
        if purge:
            self.proxy_is_purged()
        else:
            self.proxy_invalidate(force=True)

    def update(self, **updates: Any):
        """Update a bunch of attributes in a single operation."""
        with deferred_sync(self):
            for name, value in updates.items():
                if value is ...:
                    delattr(self, name)
                else:
                    setattr(self, name, value)

    @property
    def proxy_state(self) -> ProxyState:
        """Return the proxy state"""
        if self.proxy_id is None:
            return ProxyState.ERROR
        elif self.proxy_attr is None:
            return ProxyState.EMPTY
        elif self.proxy_changed is None:
            return ProxyState.CLEAN
        else:
            return ProxyState.DIRTY

    def proxy_invalidate(self, *, force=False):
        """Make this proxy object EMPTY, discarding any entity data.

        If the proxy object is DIRTY, a `InvalidationError` exception
        is raised, unless `force` is true.

        Args:
            force (bool): Invalidate even if DIRTY, without raising exception.
                Deafults to False.

        Raises:
            InvalidationError: If called on a DIRTY proxy with `force` being False
        """
        if self.proxy_id is None:
            raise ErrorState()
        if self.proxy_changed is not None and not force:
            raise InvalidationError()
        self.proxy_attr = self.proxy_changed = None

    def proxy_reset(self):
        """If proxy is EMPTY, do nothing.
        If the proxy is DIRTY, make it CLEAN by restoring the
        values changed since the last sync.
        """
        if self.proxy_id is None:
            raise ErrorState()
        if self.proxy_changed is not None:
            for name, value in self.proxy_changed.items():
                self.proxy_attr[name] = value
            self.proxy_changed = None

    def proxy_from_entity(self, entity: Any):
        """Update the proxy_attr dictionary from a given entity."""
        if self.proxy_id is None:
            raise ErrorState()
        if self.proxy_attr is None:
            self.proxy_attr = dict()
        for prop in self.proxy_schema.properties.values():
            if not prop.isId:
                prop.convert_entity_to_proxy(self, entity)

    def proxy_to_entity(
        self, attrset: set[str] | dict[str, Any] | None = None
    ) -> Entity:
        """Return an entity from the proxy values.

        Note that the entity returned will not contain the id attribute.

        Args:
            attrset (set of property names, optional): If not None,
                determines the set of names to add to the entity.

                Any type of object, where the expression
                `name in attrset` is valid, can be used.

                Use this to only add names of changed properties to
                an entity:
                self.proxy_to_entity(self.proxy_changed)

        Returns:
            entity (dict): An entity dict containing all values
                specified.
        """
        if self.proxy_id is None:
            raise ErrorState()
        entity = dict()
        for prop in self.proxy_schema.properties.values():
            if prop.isId or (attrset is not None and prop.name not in attrset):
                continue
            try:
                prop.convert_proxy_to_entity(self, entity)
            except Exception as e:
                raise ConversionError(prop, "convert_proxy_to_entity") from e
        return entity

    def proxy_is_purged(self):
        """Called to designate that this proxy is referring to a non-existent
        entity and should be marked as such.

        This type of marking happens when an entity is purged.
        """
        if self.proxy_state is ProxyState.ERROR:
            return
        self.proxy_purged_id = self.proxy_id
        self.proxy_registry.purge_proxy(self)
        self.proxy_attr = self.proxy_changed = None

    def proxy_autocommit(self):
        """Try a call to proxy_sync() if the proxy is in auto sync.

        This call is invoked whenever the proxy is changed. If the
        proxy is in autosync mode and DIRTY, the method will try to sync
        the proxy with the API. If this fails, the proxy is reset to CLEAN.

        If the proxy is not DIRTY, or not in autosync mode, the method does nothing.
        """
        if self.proxy_state is ProxyState.DIRTY and self.proxy_autosync:
            try:
                self.proxy_sync()
            except Exception:
                self.proxy_reset()
                raise

    def proxy_sync(self, entity=None):
        """Sync the data between the proxy and the API entity.

        After a sync, the proxy is CLEAN and consistent with the
        underlying entity in the Data Catalog.  This method must be
        overloaded in subclasses, to cater to the details of different
        types of entities.

        In order to sync, the method works as follows:

        1. If the proxy is DIRTY:
            - updates are sent to the API.
            - The API optionally returns a new entity object. If so, override
              the `entity` parameter.
            - Make object CLEAN (by setting proxy_changed to None)

        2. If `entity` is None: load `entity` from API

        3. Update the proxy data from `entity`. This may involve
           updating additional proxies with data contained in the given
           entity.

        For typical operations, the implementation can use the following mathods:
        ```
        self.proxy_from_entity(entity)
        self.proxy_to_entity(attrset) -> entity
        ```
        """
        raise NotImplementedError(self.__class__.__name__ + ".proxy_sync")

    def __repr__(self) -> str:
        typename = type(self).__name__
        state = self.proxy_state.name
        if self.proxy_state is ProxyState.ERROR:
            nid = f"deleted ({getattr(self, 'proxy_purged_id', '**unknown**')})"
        elif self.proxy_state is ProxyState.EMPTY:
            nid = str(self.proxy_id)
        elif self.proxy_schema.name_id is not None:
            nid = self.name
        else:
            nid = str(self.proxy_id)
        return f"<{typename} {nid} {state}>"

    def proxy_to_Series(
        self,
        *,
        sync_empty: bool = True,
        include_null: bool = False,
        include_extras: bool = False,
        simplify: bool = True,
    ) -> Series:
        """Return a pandas Series for this entity.

        The pandas Series index will contain entity fields. The values will be simplified,
        to reflect

        Arguments:
            sync_empty (bool, default=True): call proxy_sync() if state is EMPTY
            include_null (bool, default=False): include fields that evaluate to False
            include_extras (bool, default=False): also include any extras fields
            simplify (bool, default=True): return a more printable, simpler representation
        """
        import pandas as pd

        name = f"{type(self).__name__} ({self.proxy_state.name})"
        if self.proxy_state is ProxyState.ERROR or (
            not sync_empty and self.proxy_state is ProxyState.EMPTY
        ):
            return pd.Series(name=name)

        schema = self.proxy_schema

        def report_field(name):
            return include_null or bool(getattr(self, name, False))

        all_fields = [schema.id.name, *schema.properties]
        if include_extras and schema.extras is not None:
            extras = schema.extras.get(self)
            if extras is not ...:
                all_fields.remove(schema.extras.name)
                all_fields.extend(extras.keys())

        index = [name for name in all_fields if report_field(name)]
        index.sort()

        def simplified(val):
            match val:
                case Proxy(proxy_schema=schema) if schema.name_id is not None:
                    return val.name
                case Proxy():
                    return val.proxy_id
                case _:
                    return val

        def propvalue(name):
            value = getattr(self, name, ...)
            if value is not ... and simplify:
                value = simplified(value)
            return value

        data = [propvalue(name) for name in index]
        return pd.Series(index=index, data=data, name=name, dtype="object")

    @property
    def s(self) -> Series:
        return self.proxy_to_Series()

    @property
    def ss(self) -> Series:
        return self.proxy_to_Series(sync_empty=False)

    @property
    def sl(self) -> Series:
        return self.proxy_to_Series(include_null=True)

    @property
    def sx(self) -> Series:
        return self.proxy_to_Series(include_extras=True)

    @property
    def sxl(self) -> Series:
        return self.proxy_to_Series(include_null=True, include_extras=True)

    @property
    def sraw(self) -> Series:
        return self.proxy_to_Series(
            include_null=True, include_extras=True, simplify=False
        )


@contextmanager
def deferred_sync(*proxies):
    if not all(isinstance(p, Proxy) for p in proxies):
        raise TypeError("All arguments must be entity proxies")
    for i, p in enumerate(proxies):
        if any(q is p for q in proxies[i + 1 :]):
            raise ValueError(
                f"The {i}-th argument appears again; proxies must be entered once"
            )
    saved_autosync = [p.proxy_autosync for p in proxies]
    for p in proxies:
        p.proxy_autosync = False
    try:
        yield proxies
    except Exception:
        for p in proxies:
            if p.proxy_state is not ProxyState.ERROR:
                p.proxy_reset()
        raise
    finally:
        for p, a in zip(proxies, saved_autosync):
            p.proxy_autosync = a

    # This belongs outside the finally clause.
    # It will not be executed if there is an error
    exc = []
    for p in proxies:
        if p.proxy_state is ProxyState.DIRTY:
            try:
                p.proxy_sync()
            except Exception as e:
                p.proxy_reset()
                exc.append((p, e.with_traceback(None)))
        elif p.proxy_state is not ProxyState.ERROR:
            p.proxy_sync()
    if exc:
        raise RuntimeError("Failed to sync, updates reset", exc)
