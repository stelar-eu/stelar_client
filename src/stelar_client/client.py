"""
The Client class is the main STELAR API client object.

The Client class primarily holds the API URL and user credentials needed to
access the API.
"""

from urllib.parse import urljoin, urlparse
import requests

class Client:
    """An SDK (client) for the STELAR API.

    Arguments:
        base_url (str): The base URL to the STELAR installation.
        token (str): The user token issued by the KLMS SSO service.
        version (str, optional): The API version to use ('v1' or 'v2'). Defaults to 'v1'.
    """
    
    def __init__(self, base_url, token, version="v1"):
        # Validate base_url
        if not self._is_valid_url(base_url):
            raise ValueError(f"Invalid base URL: {base_url}")
        
        # Normalize base_url
        self.base_url = self._normalize_base_url(base_url)
        
        # Append version path (e.g., /api/v1 or /api/v2)
        self.version = version.lower()
        if self.version not in ["v1", "v2"]:
            raise ValueError(f"Invalid version '{self.version}'. Only 'v1' or 'v2' are supported.")
        
        self.base_url = self.base_url + f"/api/{self.version}"
        self.token = token

    @staticmethod
    def _is_valid_url(url):
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
    def _normalize_base_url(base_url):
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
        

    def request(self, method, endpoint, params=None, data=None, headers=None, json=None):
        """
        Sends a request to the STELAR API.

        Args:
            method (str): The HTTP method ('GET', 'POST', 'PUT', 'DELETE').
            endpoint (str): The API endpoint (relative to `base_url`). Can include query parameters.
            params (dict, optional): URL query parameters.
            data (dict, optional): Form data to be sent in the body.
            headers (dict, optional): Additional request headers.
            json (dict, optional): JSON data to be sent in the body.

        Returns:
            requests.Response: The response object from the API.
        """
        # Combine base_url with the endpoint
        endpoint = endpoint.lstrip('/')
        url = urljoin(self.api_url+"/", endpoint)

        # Handle query parameters in the endpoint or passed as 'params'
        if "?" in endpoint and params:
            raise ValueError("Specify query parameters either in the endpoint or in 'params', not both.")
        
        # If the URL does not contain a query, add parameters from 'params'
        if params:
            from urllib.parse import urlencode
            url = f"{url}?{urlencode(params)}"
        
        # Prepare headers, defaulting to Authorization and Content-Type
        default_headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        if headers:
            default_headers.update(headers)

        # Validate data/json and handle accordingly
        if method.upper() == "GET":
            # GET requests should not have a body (data or json)
            if data or json:
                raise ValueError("GET requests cannot include body data.")
        else:
            # POST, PUT, DELETE, etc., should use either data or json but not both
            if data and json:
                raise ValueError("Specify either 'data' or 'json', not both.")

        # Make the request using the provided method, url, params, data, json, and headers
        response = requests.request(
            method=method,
            url=url,
            params=None,  # params are already incorporated into the URL
            data=data,    # if provided, this will be form data
            json=json,    # if provided, this will be JSON payload
            headers=default_headers,
            verify=True
        )

        # Raise an exception for HTTP errors (4xx, 5xx responses)
        response.raise_for_status()
        return response

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

   