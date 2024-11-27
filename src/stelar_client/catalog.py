from base import BaseAPI
from endpoints import APIEndpointsV1
from model import Dataset, Resource, MissingParametersError, EntityNotFoundError
from requests.exceptions import HTTPError
from urllib.parse import urljoin, urlencode

class CatalogAPI(BaseAPI):
    """
    CatalogAPI is an operator used as part of the STELAR Python Client. The operator implements 
    catalog handling methods that utilize a subset of the available STELAR API Endpoints that are related
    to catalog management operations (Publishing, Searching etc.)
    """
    
    def get_dataset(self, id: str) -> Dataset:
        """Retrieves the information of a dataset as an object of the `Dataset` class.

        Args:
            id (str): The UUID or the unique name of a dataset.

        Raises:
            MissingParametersError: In case any parameters where not provided and 400 (Bad Request) was raised. 
            EntityNotFoundError: In case the API responds with 404, indicating there is not dataset with the requested ID.

        Returns:
            dataset: An object of the `Dataset` class containing the information of the retrieved dataset.
        """
        if not id:
            return None
        try:
            dataset_response = self.request("GET",  urljoin(APIEndpointsV1.GET_DATASET, id),)
            if dataset_response.status_code == 200:
                djson = dataset_response.json()['result']['dataset']
                dataset_entity = Dataset.from_dict(djson)
                return dataset_entity
        except HTTPError as he:
            if he.response.status_code == 400:
                raise MissingParametersError(f"Bad Request")
            elif he.response.status_code == 404:
                raise EntityNotFoundError(f"Entiy Not Found: {id}")