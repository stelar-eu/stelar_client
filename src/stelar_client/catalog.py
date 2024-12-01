from .base import BaseAPI
from .endpoints import APIEndpointsV1
from .model import Dataset, Resource, MissingParametersError,STELARUnknownError,DuplicateEntryError, EntityNotFoundError
from requests.exceptions import HTTPError
from urllib.parse import urljoin, urlencode

class CatalogAPI(BaseAPI):
    """
    CatalogAPI is an operator used as part of the STELAR Python Client. The operator implements 
    catalog handling methods that utilizes a subset of the available STELAR API Endpoints that are related
    to catalog management operations (Publishing, Searching etc.). It offers methods as:

    - get_dataset(id (str)) -> Dataset
    - get_datasets_dict() -> Dict(Datasets) 
    - get_datasets_list() -> List(Datasets)
    - get_resources_dict(dataset_id) -> Dict(Resource)
    - get_resources_list(dataset_id) -> List(Resource)
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
                raise EntityNotFoundError(f"Entity Not Found: {id}")
    
    def create_dataset(self, dataset: Dataset):

        if not dataset:
            return None
        try:
            publish_input = dataset.to_dict()
            dataset_response = self.request("POST",APIEndpointsV1.POST_DATASETS,json=publish_input)
            if dataset_response.status_code == 200:
                djson = dataset_response.json()['result']['dataset']
                dataset.update_from_dict(djson)
                dataset.reset_dirty()
        except HTTPError as he:
            if he.response.status_code == 400:
                raise MissingParametersError("Bad Request")
            elif he.response.status_code == 409:
                raise DuplicateEntryError("Dataset Already Exists")
            else:
                raise STELARUnknownError("Unknown Error")
            
    def get_datasets(self):
        try:
            dataset_response = self.request("GET",APIEndpointsV1.GET_DATASETS_LIST)
            if dataset_response.status_code == 200:
                datasets_list = dataset_response.json()['result']['datasets']
                dataset_object_list = [self.get_dataset(dataset) for dataset in datasets_list]
                return dataset_object_list
        except HTTPError as he:
            raise STELARUnknownError("STELAR unknown Error")
        
        
    def patch_datasets(self,dataset: Dataset):
        if not dataset:
            return None
        try:
            if dataset.is_dirty():
                json_obj = {"package_metadata":{}}
                for key,value in dataset.changes().items():
                    json_obj['package_metadata'][key] = value[1]
                
                dataset_response = self.request("PATCH",urljoin(APIEndpointsV1.PATCH_DATASET,dataset.id),json=json_obj)
                if dataset_response.status_code == 200:
                    djson = dataset_response.json()['result']['dataset']
                    dataset.update_from_dict(djson)
                    dataset.reset_dirty()
            else:
                print("No changes at Dataset Object to update")
        except HTTPError as he:
            if he.response.status_code == 404:
                raise EntityNotFoundError(f"Entity Not Found: {dataset.id}")
            else:
                raise STELARUnknownError("STELAR unknown Error")

                

    def delete_dataset(self,id: str):
        if not id:
            return None
        try:
            dataset_response = self.request("DELETE",urljoin(APIEndpointsV1.DELETE_DATASET,id))
            if dataset_response.status_code == 200:
                deleted_id = dataset_response.json()['result']['dataset']
                print(f"Dataset with id: {deleted_id} deleted successfully")
                return True
        except HTTPError as he:
            if he.response.status_code == 404:
                raise EntityNotFoundError(f"Entity Not Found: {id}")
            else:
                raise STELARUnknownError("STELAR unknown Error")


    #################################################
    ################### RESOURCES ###################
    #################################################

    def publish_dataset_resource(self,dataset: Dataset,resource: Resource):
        if not dataset or not resource:
            return None
        try:
            new_resource = resource.to_dict()
            id = dataset.id
            
            resource_response = self.request("POST",APIEndpointsV1.POST_DATASET_RESOURCE.replace("?",f"{id}"),json=new_resource)
            if resource_response.status_code == 200:
                resource_json = resource_response.json()['result']['resource']
                resource.update_from_dict(resource_json)
                resource.reset_dirty()
                dataset.resources.append(resource)

        except HTTPError as he:
            if he.response.status_code == 404:
                raise EntityNotFoundError(f"Entity not found: {id}")
            else:
                raise STELARUnknownError("STELAR unknown error")
            
    def get_dataset_resources(self,id: str,filter: str = None):
        if not id:
            return None
        
        if not filter:
            try:

                resource_response = self.request("GET",APIEndpointsV1.GET_DATASET_RESOURCES.replace("?",f"{id}"))
                if resource_response.status_code == 200:
                    resources_list = resource_response.json()['result']['resources']
                    resources_object_list = [Resource.from_dict(resource) for resource in resources_list]
                    return resources_object_list
                
            except HTTPError as he:
                if he.response.status_code == 404:
                    raise EntityNotFoundError(f"Entity not found: {id}")
                else:
                    raise STELARUnknownError("STELAR unknown error")
        else:
            try:
                resource_response = self.request("GET",APIEndpointsV1.GET_DATASET_RESOURCES_FILTER.replace("?",f"{id}")+filter)
                if resource_response.status_code == 200:
                    resources_list = resource_response.json()['result']['resources']
                    resources_object_list = [Resource.from_dict(resource) for resource in resources_list]
                    return resources_object_list
                
            except HTTPError as he:
                if he.response.status_code == 404:
                    raise EntityNotFoundError(f"Entity not found: {id}")
                else:
                    raise STELARUnknownError("STELAR unknown error")
                
    def get_resource(self,id: str):
        if not id:
            return None
        try:
            resource_response = self.request("GET",  urljoin(APIEndpointsV1.GET_RESOURCE, id),)
            if resource_response.status_code == 200:
                rjson = resource_response.json()['result']['resource']
                resource_entity = Resource.from_dict(rjson)
                return resource_entity
        except HTTPError as he:
            if he.response.status_code == 404:
                raise EntityNotFoundError(f"Entity Not Found: {id}")
            else:
                raise STELARUnknownError("STELAR unknown error")
            
    def patch_resource(self,resource: Resource):
        if not resource:
            return None
        try:
            if resource.is_dirty():
                json_obj = {"resource_metadata":{}}
                for key,value in resource.changes().items():
                    json_obj['resource_metadata'][key] = value[1]
                
                resource_response = self.request("PATCH",urljoin(APIEndpointsV1.PATCH_RESOURCE,resource.id),json=json_obj)
                if resource_response.status_code == 200:
                    djson = resource_response.json()['result']['resource']
                    resource.update_from_dict(djson)
                    resource.reset_dirty()
            else:
                print("No changes at resource Object to update")
        except HTTPError as he:
            if he.response.status_code == 404:
                raise EntityNotFoundError(f"Entity Not Found: {resource.id}")
            elif he.response.status_code == 400:
                raise MissingParametersError("Bad Request")
            else:
                raise STELARUnknownError("STELAR unknown Error")

            
    def delete_resource(self,id: str):
        if not id:
            return None
        try:
            resource_response = self.request("DELETE",urljoin(APIEndpointsV1.DELETE_RESOURCE,id))
            if resource_response.status_code == 200:
                deleted_id = resource_response.json()['result']['resource']
                print(f"Resource with id: {deleted_id} deleted successfully")
                return True
        except HTTPError as he:
            if he.response.status_code == 404:
                raise EntityNotFoundError(f"Entity Not Found: {id}")
            else:
                raise STELARUnknownError("STELAR unknown Error")


            
        


