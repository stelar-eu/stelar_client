"""
The Client class is the main STELAR API client object.

The Client class primarily holds the API URL and user credentials needed to
access the API.
"""

from urllib.parse import urljoin, urlparse
import requests
from endpoints import APIEndpointsV1

# Import subAPIs modules
from workflows import WorkflowsAPI
from catalog import CatalogAPI
from knowgraph import KnowledgeGraphAPI
from admin import AdminAPI

class Client:
    """An SDK (client) for the STELAR API.

    Arguments:
        base_url (str): The base URL to the STELAR installation.
        token (str): The user token issued by the KLMS SSO service.
        version (str, optional): The API version to use ('v1' or 'v2'). Defaults to 'v1'.
    """
    
    def __init__(self, base_url, token=None, username=None, password=None, version="v1"):
        # Validate base_url
        if not self.__is_valid_url(base_url):
            raise ValueError(f"Invalid base URL: {base_url}")
        
        # Normalize base_url
        self.base_url = self.__normalize_base_url(base_url)
        
        # Append version path (e.g., /api/v1 or /api/v2)
        self.version = version.lower()
        if self.version not in ["v1"]:
            raise ValueError(f"Invalid version '{self.version}'. Only 'v1' is supported.")
        
        self.base_url = self.base_url + f"/api/{self.version}"

        # If user provides token explicitely then use this token 
        # else if username and password was provided then initialize 
        # the subAPIs using this token for the user. 
        # 
        # Client can be also initialized without any credentials if used for specific methods provided
        if token:
            self._token = token
        elif username and password and (token is None):
            #Authenticating provides a set of tokens (an access and a refresh one used to keep the Client valid for longer periods of time)
            self.authenticate(username, password)
        else:
            self._token = None

        #Initiliaze the operators with the newly acquired token
        self.__initialize_operators()

        ####################################################################

    def __initialize_operators(self):
        ##  Instatiate the subAPIs as member variables of the client  ######
        self.workflows = WorkflowsAPI(self.api_url, token=self.token)
        self.catalog = CatalogAPI(self.api_url, token=self.token)
        self.knowledgegraph = KnowledgeGraphAPI(self.api_url, token=self.token)
        self.admin = AdminAPI(self.api_url, token=self.token)  


    def authenticate(self, username, password):
        """
        Authenticates the user and retrieves access and refresh tokens.

        This method sends a POST request to the authentication endpoint using the provided
        username and password. Upon successful authentication, the method updates the token
        property and refreshes the token for all subAPI instances.

        Args:
            username (str): The username of the user.
            password (str): The password of the user.

        Raises:
            ValueError: If either the username or password is empty.
            RuntimeError: If authentication fails due to incorrect credentials or server issues.

        Returns: 
            True: If the authentication was successful
        """
       

        if username and password:
            auth_data = {
                "username": username,
                "password": password
            }
            token_response = requests.post(url=self.base_url+APIEndpointsV1.TOKEN_ISSUE, json=auth_data, headers={"Content-Type": "application/json"})
            status_code = token_response.status_code
            token_json = token_response.json().get('result', None)
            success = token_response.json().get('success')
            
            if token_json and token_json['token'] and token_json['refresh_token'] and success and status_code == 200:
                self._token = token_json['token']
                self._refresh_token = token_json['refresh_token']

                return True

            else: 
                raise RuntimeError("Could not authenticate user. Check the provided credentials and verify the availability of the STELAR API.")
        else: 
            raise ValueError("Credentials were fully or partially empty!")


    @staticmethod
    def __is_valid_url(url):
        """
        Validates the given URL.

        Args:
            url (str): The URL to validate.

        Returns:
            bool: True if the URL is valid, False otherwise.
        """
        parsed = urlparse(url)
        return all([parsed.scheme, parsed.netloc])

    @staticmethod
    def __normalize_base_url(base_url):
        """
        Normalizes the base URL based on the following rules:
        - If base_url ends with '/stelar', do nothing.
        - If base_url ends with '/', append 'stelar'.
        - Otherwise, append '/stelar'.

        Args:
            base_url (str): The base URL to normalize.

        Returns:
            str: The normalized base URL.
        """
        if base_url.endswith('/stelar'):
            return base_url
        elif base_url.endswith('/'):
            return urljoin(base_url, 'stelar')
        else:
            return urljoin(base_url + '/', 'stelar')
        

    @property
    def api_url(self):
        """Constructs and returns the complete API URL."""
        return self.base_url

    @property
    def token(self):
        """Getter for the token property."""
        return self._token

    @token.setter
    def token(self, value):
        """
        Setter for the token property.

        Updates the token the client uses for all requests.

        Args:
            value (str): The new token to replace the existing one.

        Raises:
            ValueError: If the token is empty.
        """
        if not value:
            raise ValueError("Token cannot be empty.")
        self._token = value
        # Update subAPIs too.
        self.workflows.token = value
        self.admin.token = value
        self.catalog.token = value
        self.knowledgegraph.token = value