from functools import cached_property
from urllib.parse import urlencode, urljoin

import requests

from .proxy import Registry, RegistryCatalog
from .utils import client_for


class DefaultsRegistry(Registry):
    @cached_property
    def default_organization(self):
        return client_for(self).organizations["stelar-klms"]


class BaseAPI(RegistryCatalog):
    """Base class for all parts of the client API.

    Its main responsibility is to support API calls to the
    STELAR server. It also contains logic to manage the proxies.
    """

    def __init__(self, base_url, token, refresh_token, tls_verify=True):
        super().__init__()
        self._base_url = base_url
        self._api_url = base_url + "/api/"
        self._tls_verify = tls_verify
        self._http_session = requests.Session()
        self.reset_tokens(token, refresh_token)

    @property
    def api_url(self):
        """Return the base URL to the STELAR API"""
        return self._api_url

    @property
    def token(self):
        """Getter for the token property."""
        return self._token

    def reset_tokens(self, token, refresh_token):
        """
        Reset the primary and refresh tokens.

        Args:
            token (str): The new token for authentication
            refresh_token (str): The new refresh token
        """
        self._token = token
        self._refresh_token = refresh_token
        self._http_session.headers.update({"Authorization": f"Bearer {self._token}"})

    def request(
        self, method, endpoint, params=None, data=None, headers=None, json=None
    ):
        """
        Sends a request to the STELAR API.

        The main difference of this method with respect to `api_request` is that the
        endpoint is relative to the base URL, and it can include headers, as well as
        non-JSON data (e.g., form data).

        Args:
            method (str): The HTTP method ('GET', 'POST', 'PUT', 'DELETE').
            endpoint (str): The API endpoint (relative to `api_url`). Can include query parameters.
            params (dict, optional): URL query parameters.
            data (dict, optional): Form data to be sent in the body.
            headers (dict, optional): Additional request headers.
            json (dict, optional): JSON data to be sent in the body.

        Returns:
            requests.Response: The response object from the API.
        """
        # Validate data/json and handle accordingly
        if method.upper() == "GET":
            # GET requests should not have a body (data or json)
            if data or json:
                raise ValueError("GET requests cannot include body data.")
        else:
            # POST, PUT, DELETE, etc., should use either data or json but not both
            if data and json:
                raise ValueError("Specify either 'data' or 'json', not both.")

        # Handle query parameters in the endpoint or passed as 'params'
        if "?" in endpoint and params:
            raise ValueError(
                "Specify query parameters either in the endpoint or in 'params', not both."
            )

        # Combine base_url with the endpoint
        endpoint = endpoint.lstrip("/")
        url = urljoin(self._base_url + "/", endpoint)
        # If the URL does not contain a query, add parameters from 'params'
        if params:
            url = f"{url}?{urlencode(params)}"

        # Prepare headers, defaulting to Authorization if token is present and Content-Type
        default_headers = {
            "Content-Type": "application/json",
        }

        # if self._token:
        #    default_headers["Authorization"] = f"Bearer {self._token}"

        if headers:
            default_headers.update(headers)

        turn = 0
        while turn < 2:
            # Make the request using the provided method, url, params, data, json, and headers
            # response = requests.request(
            response = self._http_session.request(
                method=method,
                url=url,
                params=None,  # params are already incorporated into the URL
                data=data,  # if provided, this will be form data
                json=json,  # if provided, this will be JSON payload
                headers=default_headers,
                verify=self._tls_verify,
            )
            if response.status_code == 401 and turn == 0:
                # Refresh the token and try again
                self.refresh_tokens()
                # default_headers["Authorization"] = f"Bearer {self._token}"
                turn += 1
            else:
                break

        # Raise an exception for HTTP errors (4xx, 5xx responses)
        # response.raise_for_status()
        return response

    def api_request(self, method, endpoint, *, params=None, json=None):
        """Do an actual API call

        Examples:
            response = api_request("GET", "v2/datasets")
            response = api_request("POST", "v2/dataset", json={"name": "my_dataset"})

        Args:
            method (str): The HTTP method ('GET', 'POST', 'PUT', 'PATCH', 'DELETE').
            endpoint (str): The API endpoint. It should be given as a relative path.
            params (dict, optional): URL query parameters.
            json (dict, optional): JSON data to be sent in the body.
        """

        url = urljoin(self._api_url, endpoint)
        # headers = {"Authorization": f"Bearer {self._token}"}
        if params is not None and "json" in params:
            json = params["json"]

        twice = 0
        while twice < 2:
            response = self._http_session.request(
                method,
                url,
                params=params,
                json=json,
                verify=self._tls_verify,
            )
            if response.status_code == 401 and twice == 0:
                self.refresh_tokens()
                twice += 1
            else:
                break

        return response

    def GET(self, *endp, **params):
        """Send a GET request to the API.

        Examples:
            response = c.GET("v2/datasets")
            response = c.GET("v2/dataset", 'my_dataset')

        Args:
            *endp: Path components to the API endpoint.
            **params: The query parameters to send.

        Returns:
            requests.Response: The response object from the API.
        """
        endpoint = "/".join(str(pc) for pc in endp)
        return self.api_request("GET", endpoint, params=params)

    def POST(self, *endp, params={}, **json):
        """Send a POST request to the API.

        Example:
            response = c.POST("v2/dataset", name="my_dataset")

        Args:
            *endp: Path components to the API endpoint.
            params: (keyword-only) The query parameters to send.
            **json: The JSON data to send.

        Returns:
            requests.Response: The response object from the API.
        """
        endpoint = "/".join(str(pc) for pc in endp)
        return self.api_request("POST", endpoint, params=params, json=json)

    def PUT(self, *endp, params={}, **json):
        """Send a PUT request to the API.

        Example:
            response = c.PUT("v2/tag", "my_tag", display_name="My Tag", vocabulary_id='my_vocabulary')

        Args:
            *endp: Path components to the API endpoint.
            params: (keyword-only) The query parameters to send.
            **json: The JSON data to send.

        Returns:
            requests.Response: The response object from the API.
        """
        endpoint = "/".join(str(pc) for pc in endp)
        return self.api_request("PUT", endpoint, params=params, json=json)

    def PATCH(self, *endp, params={}, **json):
        """Send a PATCH request to the API.

        Example:
            response = c.PATCH("v2/dataset", "my_dataset", author="John Doe")

        Args:
            *endp: Path components to the API endpoint.
            params: (keyword-only) The query parameters to send.
            **json: The JSON data to send.
        Returns:
            requests.Response: The response object from the API.
        """
        endpoint = "/".join(str(pc) for pc in endp)
        return self.api_request("POST", endpoint, params=params, json=json)

    def DELETE(self, *endp, **params):
        """Send a DELETE request to the API.

        Example:
            response = c.DELETE("v2/dataset", "my_dataset")

        Args:
            *endp: Path components to the API endpoint.
            **params: The query parameters to send.
        Returns:
            requests.Response: The response object from the API.
        """
        endpoint = "/".join(str(pc) for pc in endp)
        return self.api_request("DELETE", endpoint, params=params)

    @property
    def api(self):
        from .api_call import api_call

        return api_call(self)
