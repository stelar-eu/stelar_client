import requests
from urllib.parse import urljoin, urlencode
from typing import List, Dict




class Resource:
    """
    A class representing a STELAR resource with metadata and additional details.
    Objects of this class are used for holding metadata information of a STELAR resource entity
    during the usage of the client in a local runtime.
    """

    def __init__(self, url: str, format: str, name: str) -> None:
        self.id = None
        self.url = url
        self.format = format
        self.name = name
        pass


    def __str__(self):
        return f"Resource ID: {self.id} | Name: {self.name} | URL: {self.url} | Format : {self.format}"
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            url=data.get('url'),
            format=data.get('format'),
            name=data.get('name'),
        )._populate_additional_fields(data)
    
    def _populate_additional_fields(self, data: dict):
        self.id = data.get('id')
        self.relation = data.get('relation')
        self.package_id = data.get('package_id')
        self.modified_date = data.get('metadata_modified')
        self.creation_date = data.get('created')
        self.description = data.get('description')
        return self



class Dataset:
    """
    A class representing a STELAR dataset with metadata, resources, and additional details.
    Objects of this class are used for holding metadata information of a STELAR dataset entity
    during the usage of the client in a local runtime.
    """
    @classmethod
    def from_dict(cls, data: dict):
        """
        A class method for constructing a Dataset holder when fetching metadata from the STELAR API.
        This constructor is mainly used by the operators of the STELAR Client to achieve consistency
        and availability of the metadata held in a local Dataset object during all operations related
        to transacting the information between the local runtime and the STELAR API.

        Args:he name of the dataset.
            tags (list): A list of tags (str) associated with the dataset.
            title (str): The title of the dataset.
            notes (str): A description or notes about the dataset.
            modified_date (str): The last modified date of the dataset.
            creation_date (str): The creation date of the dataset.
            num_tags (int): The number of tags associated with the dataset.
            num_resources (int): The number of resources in the dataset.
            creation_user_id (str): The ID of the user who created the dataset.
            url (str): The URL associated with the dataset.
            extras List[Dict]: Additional metadata for the dataset.(spatial, theme, language etc.)
            resources (List[Resources]): A list of Resource objects related to the dataset.
        """
        tags = [tag.get("name") for tag in data.get("tags", [])]
        extras = {extra.get("key"): extra.get("value") for extra in data.get("extras", [])}
        resources = [Resource.from_dict(resource) for resource in data.get("resources", [])]

        return cls(
            title=data.get('title'),
            notes=data.get('notes'),
            tags=tags,
            extras=extras,
            resources=resources,
        )._populate_additional_fields(data)

    def _populate_additional_fields(self, data: dict):
        self.id = data.get('id')
        self.name = data.get('name')
        self.modified_date = data.get('metadata_modified')
        self.creation_date = data.get('metadata_created')
        self.num_tags = data.get('num_tags')
        self.num_resources = data.get('num_resources')
        self.creation_user_id = data.get('author')
        self.url = data.get('url')
        return self
    
    def __init__(self, title: str, notes: str, tags: List[str], extras: Dict = None, profile: Resource = None, resources: List[Resource] = None):
        """
        Initializes an instance of the Dataset class.

        Args:
            title (str): The title of the dataset.
            notes (str): A description or notes about the dataset.
            tags (list): A list of tags (str) associated with the dataset.
            extras (dict): Additional metadata (spatial, theme, language etc.) for the dataset.
            profile (Resource): A profile Resource related to the dataset.
            resources (List[Resource]): A list of resources to be included in the dataset.
        """
        self.id = None
        self.name = None
        self.modified_date = None
        self.title = title
        self.notes = notes
        self.tags = tags
        self.extras = extras
        self.profile = profile
        self.resources = resources


    def __str__(self):
        dataset_info = f"Title: {self.title} | Dataset ID: {self.id} | Name: {self.name} | Tags: {self.tags} | Modified Date: {self.modified_date}\nDataset Resources:\n"
        if self.resources :
            for resource in self.resources:
                dataset_info = dataset_info + "\t" + str(resource) + "\n"
        else:
            dataset_info = dataset_info + "\tNo Resources Associated"
        return dataset_info



class MissingParametersError(Exception):
    pass

class DuplicateEntryError(Exception):
    pass

class STELARUnknownError(Exception):
    pass

class EntityNotFoundError(Exception):
    pass