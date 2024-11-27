from base import BaseAPI
from endpoints import APIEndpointsV1
from model import Dataset, Resource, MissingParametersError, EntityNotFoundError
from requests.exceptions import HTTPError
from urllib.parse import urljoin, urlencode

class CatalogAPI(BaseAPI):

    
    def get_dataset(self, id: str):
        if not id:
            return None
        
        try:
            dataset_response = self.request("GET",  urljoin(APIEndpointsV1.GET_DATASET, id),)
            if dataset_response.status_code == 200:
                djson = dataset_response.json()['result']['dataset']
                if djson.get("tags"):
                    djson["tags"] = [tag.get("name") for tag in djson["tags"]]
                if djson.get("extras"):
                    djson["extras"] = { extra.get("key"): extra.get("value") for extra in djson["extras"]}

                if djson.get("resources"):
                    djson["resources"] = [
                        Resource.fetching_constructor(
                            resource.get('url'),
                            resource.get('package_id'),
                            resource.get('metadata_modified'),
                            resource.get('created'),
                            resource.get('format'),
                            resource.get('description'),
                            resource.get('id'),
                            resource.get('name'),
                            resource.get('relation')
                        ) for resource in djson['resources']
                    ]
                
                dataset_entity = Dataset.fetching_constructor(djson.get('id'),
                                                              djson.get('name'),
                                                              djson.get('tags'),
                                                              djson.get('title'),
                                                              djson.get('notes'),
                                                              djson.get('metadata_modified'),
                                                              djson.get('metadata_created'),
                                                              djson.get('num_tags'),
                                                              djson.get('num_resources'),
                                                              djson.get('author'),
                                                              djson.get('url'),
                                                              djson.get('extras'),
                                                              djson.get('resources')
                                                              )
                return dataset_entity
            
        except HTTPError as he:
            if he.response.status_code == 400:
                raise MissingParametersError(f"Bad Request")
            elif he.response.status_code == 404:
                raise EntityNotFoundError(f"Entiy Not Found: {id}")
        