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
    def fetching_constructor(cls, url: str, package_id: str, modified_date: str,
                             creation_date: str, format: str, description: str, id: str, 
                             name: str = None, relation: str = None):
        resource = cls(url=url, format=format, name=name)
        resource.id = id
        resource.relation = relation
        resource.package_id = package_id
        resource.modified_date = modified_date
        resource.creation_date = creation_date
        resource.description = description
        
        return resource





class Dataset:
    """
    A class representing a STELAR dataset with metadata, resources, and additional details.
    Objects of this class are used for holding metadata information of a STELAR dataset entity
    during the usage of the client in a local runtime.
    """
    @classmethod
    def fetching_constructor(cls, id: str, name: str, tags: List[str], title: str, notes: str, 
                             modified_date: str, creation_date: str, num_tags: int, 
                             num_resources: int, creation_user_id: str, url: str = None, 
                             extras: List[Dict]=None, resources: List[Resource]=None):        
        """
        A class method for constructing a Dataset holder when fetching metadata from the STELAR API.
        This constructor is mainly used by the operators of the STELAR Client to achieve consistency
        and availability of the metadata held in a local Dataset object during all operations related
        to transacting the information between the local runtime and the STELAR API.

        Args:
            id (str): The unique identifier of the dataset.
            name (str): The name of the dataset.
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

        dataset = cls(title=title, notes=notes, tags=tags, extras=extras, resources=resources)
        dataset.id = id
        dataset.name = name
        dataset.modified_date = modified_date
        dataset.creation_date = creation_date
        dataset.num_tags = num_tags
        dataset.num_resources = num_resources
        dataset.creation_user_id = creation_user_id
        dataset.url = url
        dataset.extras = extras
        
        return dataset

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
        return dataset_info



class MissingParametersError(Exception):
    pass

class DuplicateEntryError(Exception):
    pass

class STELARUnknownError(Exception):
    pass

class EntityNotFoundError(Exception):
    pass