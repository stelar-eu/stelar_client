from base import BaseAPI
from endpoints import APIEndpointsV1
from urllib.parse import urljoin, urlencode

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