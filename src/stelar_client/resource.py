from typing import List, Dict
from IPython.core.display import HTML
from IPython.display import display


class Resource:
    """
    A class representing a STELAR resource with metadata and additional details.

    This class is designed to hold metadata for a STELAR resource entity, making it easier
    to manage and manipulate resource information within the client application runtime.
    """

    def __init__(self, url: str, format: str, name: str) -> None:
        """
        Initialize a Resource instance with essential fields.

        Args:
            url (str): The URL where the resource is located.
            format (str): The format of the resource.
            name (str): The name of the resource.
            kwargs: Additional optional fields.
        """
        self._data = {
            "url": url,
            "format": format,
            "name": name
        }
        self._original_data = self._data.copy()  # Copy for dirty tracking
        self._dirty_fields = set()  # Track which fields have been modified

        # Additional fields
        self.id = None
        self.relation = None
        self.package_id = None
        self.modified_date = None
        self.creation_date = None
        self.description = None

    def __getattr__(self, name):
        """Handle attribute access dynamically."""
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'Resource' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        """Handle attribute assignment dynamically."""
        if name in {"_data", "_original_data", "_dirty_fields"} or name not in self._data:
            super().__setattr__(name, value)
        else:
            # Only mark as dirty if the value actually changes
            if self._data[name] != value:
                self._data[name] = value
                self._dirty_fields.add(name)

    def is_dirty(self):
        """Check if any field is dirty."""
        return bool(self._dirty_fields)

    def changes(self):
        """Return the fields that have been modified and their changes."""
        return {
            key: (self._original_data[key], self._data[key])
            for key in self._dirty_fields
        }

    def reset_dirty(self):
        """Reset the dirty state and save the current data as original."""
        self._original_data = self._data.copy()
        self._dirty_fields.clear()

    @classmethod
    def from_dict(cls, data: dict):
        """
        A class method to construct a Resource instance from a dictionary.

        Args:
            data (dict): The dictionary containing resource metadata.

        Returns:
            Resource: A fully constructed Resource instance.
        """
        instance = cls(
            url=data.get('url'),
            format=data.get('format'),
            name=data.get('name'),
        )
        instance._populate_additional_fields(data)
        return instance

    def _populate_additional_fields(self, data: dict):
        """
        Populate additional fields of the Resource object.

        Args:
            data (dict): The dictionary containing resource metadata.
        """
        self.id = data.get('id')
        self.relation = data.get('relation')
        self.package_id = data.get('package_id')
        self.modified_date = data.get('metadata_modified')
        self.creation_date = data.get('created')
        self.description = data.get('description')
        return self

    def to_dict(self):
        """
        Convert the Resource instance into a dictionary.

        Returns:
            dict: A dictionary representation of the Resource instance.
        """
        resource_dict = {
            "resource_metadata":{
                "url": self.url,
                "format": self.format,
                "name": self.name,
            }   
        }
        return resource_dict

    def update_from_dict(self, data: dict):
        """
        Updates the current Resource instance with new data from a dictionary.

        Args:
            data (dict): A dictionary containing new data for the Resource.
        """
        for key in ['url', 'format', 'name']:
            if key in data:
                setattr(self, key, data[key])

        # Update additional fields
        self._populate_additional_fields(data)

    def __str__(self):
        """
        Provide a human-readable string representation of the Resource instance.

        Returns:
            str: A string describing the resource's key attributes.
        """
        return f"Resource ID: {self.id} | Relation: {self.relation} | Name: {self.name} | URL: {self.url} | Format : {self.format}"

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
                        <td style="text-align: left; padding: 5px; border: 1px solid #ddd;">{self.package_id or 'N/A'}</td>
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
