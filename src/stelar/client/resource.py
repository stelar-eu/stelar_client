from typing import Any

from IPython.core.display import HTML

from .generic import GenericCursor, GenericProxy, generic_proxy_sync
from .proxy import (
    DateField,
    ExtrasProperty,
    Id,
    IntField,
    Property,
    Proxy,
    Reference,
    StrField,
)


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


class Resource(GenericProxy):
    """
    A proxy for a STELAR resource with metadata and additional details.
    """

    id = Id()
    dataset = Reference("Dataset", entity_name="package_id", trigger_sync=True)
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
        if self.proxy_autosync:
            self.proxy_sync()

    def __delattr__(self, attr):
        if attr.startswith("proxy_") or attr in self.proxy_schema.all_fields:
            return object.__delattr__(self, attr)

        prop = self.proxy_schema.extras
        extras = prop.get(self)
        if attr in extras:
            prop.touch(self)
            del extras[attr]
            if self.proxy_autosync:
                self.proxy_sync()
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
        # Define the watermark image URL (Replace with your image path)
        watermark_image_url = "logo.png"

        # Build the table HTML
        html = f"""
        <div style="position: relative; width: 100%; height: auto; display: flex; justify-content: flex-start; align-items: flex-start; margin-bottom: 20px;">
            <table border="1" style="
                border-collapse: collapse;
                width: 50%;
                margin: 0;
                color: black;
                background-image: url('{watermark_image_url}');
                background-size: 20%;
                background-position: center;
                background-repeat: no-repeat;">
                <thead>
                    <tr>
                        <th colspan="2" style="text-align: center; padding: 10px; font-size: 18px; font-weight: bold; background-color: rgba(242, 242, 242, 0.8);">
                            Resource Summary
                        </th>
                    </tr>
                    <tr style="background-color: rgba(242, 242, 242, 0.8);">
                        <th style="width: 50%; text-align: center;">Attribute</th>
                        <th style="width: 50%; text-align: center;">Value</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="background-color: rgba(255, 255, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">ID:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.id or 'N/A'}</td>
                    </tr>
                    <tr style="background-color: rgba(230, 179, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">Parent Package:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.dataset.id or 'N/A'}</td>
                    </tr>
                    <tr style="background-color: rgba(255, 255, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">Relation To Parent:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.relation or 'N/A'}</td>
                    </tr>
                    <tr style="background-color: rgba(230, 179, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">Name:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.name}</td>
                    </tr>
                    <tr style="background-color: rgba(255, 255, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">URL:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;"><a href="{self.url}" target="_blank">{self.url}</a></td>
                    </tr>
                    <tr style="background-color: rgba(230, 179, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">Format:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.format}</td>
                    </tr>
                    <tr style="background-color: rgba(255, 255, 255, 0.8);">
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd; font-weight: bold;">Description:</td>
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.description or 'N/A'}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
        return HTML(html)._repr_html_()


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

    def for_object(self, s3obj):
        pass
