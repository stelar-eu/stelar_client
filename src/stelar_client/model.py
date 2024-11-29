from typing import List, Dict
from IPython.core.display import HTML

class Resource:
    """
    A class representing a STELAR resource with metadata and additional details.

    This class is designed to hold metadata for a STELAR resource entity, making it easier
    to manage and manipulate resource information within the client application runtime.

    Attributes:
        id (str): The unique identifier for the resource.
        url (str): The URL where the resource is located.
        format (str): The format of the resource (e.g., "CSV", "JSON").
        name (str): The name of the resource.
    """


    def __init__(self, url: str, format: str, name: str) -> None:
        """
    Initialize a Resource instance with essential fields.

    Args:
        url (str): The URL where the resource is located.
        format (str): The format of the resource.
        name (str): The name of the resource.
    """
        self.id = None
        self.url = url
        self.format = format
        self.name = name
        pass


    def __str__(self):
        """
        Provide a human-readable string representation of the Resource instance.

        Returns:
            str: A string describing the resource's key attributes.
        """
        return f"Resource ID: {self.id} | Name: {self.name} | URL: {self.url} | Format : {self.format}"
    
    @classmethod
    def from_dict(cls, data: dict):
        """
        A class method to construct a Resource instance from a dictionary.

        Args:
            data (dict): The dictionary containing resource metadata.

        Returns:
            Resource: A fully constructed Resource instance.
        """
        return cls(
            url=data.get('url'),
            format=data.get('format'),
            name=data.get('name'),
        )._populate_additional_fields(data)
    

    def _populate_additional_fields(self, data: dict):
        """
        A helper method to populate additional fields from the dictionary.

        This is used internally by the `from_dict` method to set optional fields
        that aren't part of the main constructor.

        Args:
            data (dict): The dictionary containing resource metadata.

        Returns:
            Resource: The updated Resource instance (self).
        """
        self.id = data.get('id')
        self.relation = data.get('relation')
        self.package_id = data.get('package_id')
        self.modified_date = data.get('metadata_modified')
        self.creation_date = data.get('created')
        self.description = data.get('description')
        return self
    
    def update_from_dict(self, data: dict):
        """
        Updates the current Resource instance with new data from a dictionary.

        Args:
            data (dict): A dictionary containing new data for the Resource.
        """
        # Update the primary fields of the Resource
        for key in ['url', 'format', 'name']:
            if key in data:
                setattr(self, key, data[key])

        # Update the additional fields
        self._populate_additional_fields(data)

        
    def _repr_html_(self):
        """
        Provide an HTML representation of the Resource instance for Jupyter display.
        """
        html = f"""
        <table border="1" style="border-collapse: collapse; width: 50%; text-align: left;">
            <tr><th>Attribute</th><th>Value</th></tr>
            <tr><td>ID</td><td>{self.id or 'N/A'}</td></tr>
            <tr><td>Parent Package</td><td>{self.package_id}</td></tr>
            <tr><td>Relation To Parent</td><td>{self.relation}</td></tr>
            <tr><td>Name</td><td>{self.name}</td></tr>
            <tr><td>URL</td><td><a href="{self.url}" target="_blank">{self.url}</a></td></tr>
            <tr><td>Format</td><td>{self.format}</td></tr>
        </table>
        """
        return HTML(html)._repr_html_()

    def to_dict(self):
        """
        Convert the Resource instance into a dictionary.
        """
    
        json_dict = {
            "resource_metadata": {
                "url": self.url,
                "name": self.name,
                "format": self.format,
            }
        
        
        }
        return json_dict



class Dataset:
    """
    A class representing a STELAR dataset with metadata, resources, and additional details.
    """
    def __init__(self, title: str, notes: str, tags: List[str], extras: Dict = None, profile=None, resources: List = None):
        """
        Initializes an object of the Dataset class.
        """
        self._data = {
            "title": title,
            "notes": notes,
            "tags": tags,
            "extras": extras,
            "profile": profile,
            "resources": resources,
        }
        self._original_data = self._data.copy()  # Copy for dirty tracking
        self._dirty_fields = set()  # Track which fields have been modified

        # Additional fields
        self.id = None
        self.name = None
        self.modified_date = None
        self.creation_date = None
        self.num_tags = None
        self.num_resources = None
        self.creation_user_id = None
        self.url = None

    def __getattr__(self, name):
        """Handle attribute access dynamically."""
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'Dataset' object has no attribute '{name}'")

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
        A class method for constructing a Dataset object from a dictionary of metadata.
        """
        tags = [tag.get("name") for tag in data.get("tags", [])]
        extras = {extra.get("key"): extra.get("value") for extra in data.get("extras", [])}
        resources = [Resource.from_dict(resource) for resource in data.get("resources", [])]

        instance = cls(
            title=data.get('title'),
            notes=data.get('notes'),
            tags=tags,
            extras=extras,
            resources=resources,
        )
        instance._populate_additional_fields(data)
        return instance

    def _populate_additional_fields(self, data: dict):
        """
        Populate additional fields of the Dataset object.
        """
        self.id = data.get('id')
        self.name = data.get('name')
        self.modified_date = data.get('metadata_modified')
        self.creation_date = data.get('metadata_created')
        self.num_tags = data.get('num_tags')
        self.num_resources = data.get('num_resources')
        self.creation_user_id = data.get('author')
        self.url = data.get('url')
        return self

    def to_dict(self):
        """
        Convert the Dataset instance into a dictionary.
        """
        if self.extras:
            json_dict = {
                "basic_metadata": {
                    "title": self.title,
                    "notes": self.notes,
                    "tags": self.tags,
                },
                "extra_metadata": self.extras,
            }
        else:
            json_dict = {
                "basic_metadata": {
                    "title": self.title,
                    "notes": self.notes,
                    "tags": self.tags,
                }
            }
        return json_dict

    def update_from_dict(self, data: dict):
        """
        Updates the current Dataset instance with new data from a dictionary.
        """
        for key in ['title', 'notes', 'tags', 'extras', 'resources']:
            if key in data:
                setattr(self, key, data[key])

        # Update additional fields
        self._populate_additional_fields(data)

    
    def _repr_html_(self):
        """
        Provide an HTML representation of the Dataset instance for Jupyter display.
        """
        resources_html = ""
        if self.resources:
            resources_html = "".join(
                f"""
                <tr>
                    <td>{resource.id or 'N/A'}</td>
                    <td>{resource.name}</td>
                    <td><a href="{resource.url}" target="_blank">{resource.url}</a></td>
                    <td>{resource.format}</td>
                </tr>
                """
                for resource in self.resources
            )
        else:
            resources_html = "<tr><td colspan='4'>No Resources Associated</td></tr>"

        html = f"""
        <strong>Dataset Summary:</strong>
        <table>
            <tr><th>Attribute</th><th>Value</th></tr>
            <tr><td>ID</td><td>{self.id or 'N/A'}</td></tr>
            <tr><td>Title</td><td>{self.title}</td></tr>
            <tr><td>Notes</td><td>{self.notes}</td></tr>
            <tr><td>Tags</td><td>{', '.join(self.tags)}</td></tr>
            <tr><td>Modified Date</td><td>{self.modified_date or 'N/A'}</td></tr>
        </table>
        <br>
        <strong>Dataset Resources:</strong>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr><th>ID</th><th>Name</th><th>URL</th><th>Format</th></tr>
            {resources_html}
        </table>
        """
        return HTML(html)._repr_html_()
    
    def __str__(self):
        dataset_info = f"Title: {self.title} | Dataset ID: {self.id} | Name: {self.name} | Tags: {self.tags} | Modified Date: {self.modified_date}\nDataset Resources:\n"
        if self.resources:
            for resource in self.resources:
                dataset_info += "\t" + str(resource) + "\n"
        else:
            dataset_info += "\tNo Resources Associated"
        return dataset_info




class MissingParametersError(Exception):
    pass

class DuplicateEntryError(Exception):
    pass

class STELARUnknownError(Exception):
    pass

class EntityNotFoundError(Exception):
    pass