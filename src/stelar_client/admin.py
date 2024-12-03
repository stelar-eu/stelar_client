from .base import BaseAPI
from .endpoints import APIEndpointsV1
from .model import Policy,MissingParametersError,STELARUnknownError,DuplicateEntryError, EntityNotFoundError
from urllib.parse import urljoin, urlencode
from requests.exceptions import HTTPError
import yaml

class AdminAPI(BaseAPI):

    def get_user_by_id(self, user_id: str) -> dict:
        """Returns a user entity by UUID or by username. Requires admin rights.
        
        Args: 
            user_id (str): User UUID or username.
        
        Returns: 
            dict: The user representation in dictionary resembling JSON.
        """
        
        response = self.request("GET", urljoin(APIEndpointsV1.GET_USER, user_id))
        if response.status_code == 200:
            result = response.json().get('result',  None)
            if result:
                userRepresentation = result.get('user', None)
                return userRepresentation    
        else:
            return response.json()
        


    def get_users(self, offset: int = None, limit: int = None) -> dict:
        """Returns all user entities present inside the KLMS. Requires admin rights.
        
        Args: 
            offset (int): Optional offset parameter to apply pagination logic.
            limit (int): Optional limit parameter to apply pagination. If not set, all users will be returned
        
        Returns: 
            dict: The user representations in dictionary resembling JSON.
        """
        
        response = self.request("GET", APIEndpointsV1.GET_USERS)
        if response.status_code == 200:
            result = response.json().get('result',  None)
            if result:
                userRepresentation = result.get('users', None)
                return userRepresentation
        else:
            return response.json()
        

    def create_policy(self,policy: Policy):

        if not policy:
            return None
        try:
            yaml_headers = {"Content-Type": "application/x-yaml"}
            policy_response = self.request("POST",APIEndpointsV1.POST_POLICY,headers=yaml_headers,data=policy.policy_content)
            if policy_response.status_code == 200:
                print(yaml.dump(policy_response.json()['result']['policy']))
                # dataset.update_from_dict(djson)
                # dataset.reset_dirty()
        except HTTPError as he:
            if he.response.status_code == 400:
                raise MissingParametersError("Bad Request")
            elif he.response.status_code == 409:
                raise DuplicateEntryError("Dataset Already Exists")
            else:
                raise STELARUnknownError(f"Unknown Error: {he}")
            
            
    def get_policy_info(self,filter: str):
        if not filter:
            return None
        try:
            policy_repr = self.request("GET",urljoin(APIEndpointsV1.GET_POLICY_REPRESENATION,filter))
            policy_info = self.request("GET",urljoin(APIEndpointsV1.GET_POLICY_INFO,filter))
            if policy_info.status_code == 200 and policy_repr.status_code == 200:
                yaml_content = policy_repr.content
                if yaml_content.startswith(b"b'"):
                    yaml_content = yaml_content[2:-1]
        
                formatted_yaml_string = yaml_content.decode('unicode_escape')
                pjson = policy_info.json()['result']['policy']
                pjson['policy_content'] = formatted_yaml_string
                policy_obj = Policy.from_dict(pjson)
                return policy_obj
        except HTTPError as he:
            if he.response.status_code == 400:
                raise MissingParametersError("Bad Request")
            elif he.response.status_code == 409:
                raise DuplicateEntryError("Dataset Already Exists")
            else:
                raise STELARUnknownError(f"Unknown Error: {he}")
    
    def get_policy_representation(self,filter: str):
        if not filter:
            return None
        try:
            policy_repr = self.request("GET",urljoin(APIEndpointsV1.GET_POLICY_REPRESENATION,filter))
            if policy_repr.status_code == 200:
                yaml_content = policy_repr.content
                if yaml_content.startswith(b"b'"):
                    yaml_content = yaml_content[2:-1]
        
                formatted_yaml_string = yaml_content.decode('unicode_escape')
                print(formatted_yaml_string)
        except HTTPError as he:
            if he.response.status_code == 400:
                raise MissingParametersError("Bad Request")
            elif he.response.status_code == 409:
                raise DuplicateEntryError("Dataset Already Exists")
            else:
                raise STELARUnknownError(f"Unknown Error: {he}")

     
    def get_policy_list(self):
        try:
            policy_response = self.request("GET",APIEndpointsV1.GET_POLICY_LIST)
            if policy_response.status_code == 200:
                pjson = policy_response.json()['result']['policies']
                policy_list = [json for json in pjson]
                Policy.present_dictionaries_as_tables(policy_list)
        except HTTPError as he:
            if he.response.status_code == 400:
                raise MissingParametersError("Bad Request")
            elif he.response.status_code == 409:
                raise DuplicateEntryError("Dataset Already Exists")
            else:
                raise STELARUnknownError(f"Unknown Error: {he}")


