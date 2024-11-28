import requests
from urllib.parse import urljoin, urlencode
from typing import List, Dict
import json




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


# class Dataset:
#     """
#     A class representing a STELAR dataset with metadata, resources, and additional details.
#     Objects of this class are used for holding metadata information of a STELAR dataset entity
#     during the usage of the client in a local runtime.
#     """
#     @classmethod
#     def from_dict(cls, data: dict):
#         """
#         A class method for constructing a Dataset object from a dictionary of metadata.

#         This method is used to parse JSON data received from the STELAR API and
#         construct a Dataset object that maintains consistency and integrity of metadata
#         in a local runtime environment.

#         Args:
#             data (dict): The dictionary containing dataset metadata fetched from the API.
#                         It includes fields such as tags, extras, resources, and other dataset properties.

#         Returns:
#             Dataset: An instance of the Dataset class populated with the parsed metadata.
#         """
#         tags = [tag.get("name") for tag in data.get("tags", [])]
#         extras = {extra.get("key"): extra.get("value") for extra in data.get("extras", [])}
#         resources = [Resource.from_dict(resource) for resource in data.get("resources", [])]

#         return cls(
#             title=data.get('title'),
#             notes=data.get('notes'),
#             tags=tags,
#             extras=extras,
#             resources=resources,
#         )._populate_additional_fields(data)

#     def _populate_additional_fields(self, data: dict):
#         """
#         A helper method to populate additional fields of the Dataset object.
#         This is used internally after the primary construction to set fields
#         not directly passed in the constructor.

#         Args:
#             data (dict): The raw dictionary representing the dataset metadata from the API.

#         Returns:
#             Dataset: The updated Dataset instance (self).
#         """
#         self.id = data.get('id')
#         self.name = data.get('name')
#         self.modified_date = data.get('metadata_modified')
#         self.creation_date = data.get('metadata_created')
#         self.num_tags = data.get('num_tags')
#         self.num_resources = data.get('num_resources')
#         self.creation_user_id = data.get('author')
#         self.url = data.get('url')
#         return self
    

#     def to_dict(self):
#         if self.extras:
#             json_dict = {
#                 "basic_metadata":{
#                     "title":self.title,
#                     "notes":self.notes,
#                     "tags":self.tags
#                 },
#                 "extra_metadata": self.extras

#             }
#         else:
#             json_dict = {
#                 "basic_metadata":{
#                     "title":self.title,
#                     "notes":self.notes,
#                     "tags":self.tags
#                 }
#             }
           
#         return json_dict
    
#     def update_from_dict(self, data: dict):
#         """
#         Updates the current Dataset instance with new data from a dictionary.

#         Args:
#             data (dict): The dictionary containing updated dataset metadata.

#         Returns:
#             None: Updates the instance in place.
#         """
#         if 'title' in data:
#             self.title = data['title']
#         if 'notes' in data:
#             self.notes = data['notes']
#         if 'tags' in data:
#             self.tags = [tag.get("name") for tag in data.get("tags", [])]
#         if 'extras' in data:
#             self.extras = {extra.get("key"): extra.get("value") for extra in data.get("extras", [])}
#         if 'resources' in data:
#             self.resources = [Resource.from_dict(resource) for resource in data.get("resources", [])]
        
#         # Update additional fields
#         self._populate_additional_fields(data)

        
#     def __init__(self, title: str, notes: str, tags: List[str], extras: Dict = None, profile: Resource = None, resources: List[Resource] = None):
#         """
#         Initializes an object of the Dataset class.

#         Args:
#             title (str): The title of the dataset.
#             notes (str): A description or notes about the dataset.
#             tags (list): A list of tags (str) associated with the dataset.
#             extras (dict): Additional metadata (spatial, theme, language etc.) for the dataset.
#             profile (Resource): A profile Resource related to the dataset.
#             resources (List[Resource]): A list of resources to be included in the dataset.
#         """
#         self.id = None
#         self.name = None
#         self.modified_date = None
#         self.title = title
#         self.notes = notes
#         self.tags = tags
#         self.extras = extras
#         self.profile = profile
#         self.resources = resources


#     def __str__(self):
#         dataset_info = f"Title: {self.title} | Dataset ID: {self.id} | Name: {self.name} | Tags: {self.tags} | Modified Date: {self.modified_date}\nDataset Resources:\n"
#         if self.resources :
#             for resource in self.resources:
#                 dataset_info = dataset_info + "\t" + str(resource) + "\n"
#         else:
#             dataset_info = dataset_info + "\tNo Resources Associated"
#         return dataset_info

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