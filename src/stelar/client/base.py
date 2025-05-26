import re
import time
from typing import Type, TypeVar
from urllib.parse import urlencode, urljoin

import requests

from .proxy import Proxy, ProxyCursor, RegistryCatalog

ProxyClass = TypeVar("ProxyClass", bound="Proxy")


class KLMSInfo:
    def __init__(self, info: dict):
        self.__dict__.update(info)

    def __repr__(self):
        return f"<KLMSInfo {self.__dict__}>"

    def __str__(self):
        return str(self.__dict__)

    def _repr_pretty_(self, p, cycle: bool):
        for k, v in self.__dict__.items():
            p.text(f"{k}: {v}")
            p.break_()


class BaseAPI(RegistryCatalog):
    """Base class for all parts of the client API.

    Its main responsibility is to support API calls to the
    STELAR server. It also contains logic to manage the proxies.
    """

    def __init__(self, base_url, token_json, tls_verify=True):
        super().__init__()
        self._base_url = base_url
        self._api_url = base_url + "/api/"
        self._tls_verify = tls_verify
        self._http_session = requests.Session()
        self.reset_tokens(token_json)

        # Initialize the default organization
        self._info = self._get_api_info()

    def _get_api_info(self):
        help = self.request("GET", "help").json()["result"]
        info_attr = {
            k: v for k, v in help.items() if re.match(r"[A-Za-z][A-Za-z0-9_]*", k)
        }
        from importlib.metadata import version

        info_attr["client_version"] = version("stelar.client")
        return KLMSInfo(info_attr)

    @property
    def klms_info(self):
        return self._info

    @property
    def api_url(self):
        """Return the base URL to the STELAR API"""
        return self._api_url

    @property
    def token(self):
        """Getter for the token property."""
        return self._token

    def reset_tokens(self, token_json):
        """
        Reset the primary and refresh tokens.

        Args:
            token_json: The token response for authentication
        """
        token = token_json.get("token")
        refresh_token = token_json.get("refresh_token")
        expires_in = token_json.get("expires_in")
        refresh_expires_in = token_json.get("refresh_expires_in")

        self._token_json = token_json
        self._token = token
        self._refresh_token = refresh_token
        self._http_session.headers.update({"Authorization": f"Bearer {self._token}"})

        self._expires_in = expires_in
        self._refresh_expires_in = refresh_expires_in
        self._token_reset_time = time.time()
        self._expiration_time = self._token_reset_time + self._expires_in * 0.9
        self._refresh_expiration_time = (
            self._token_reset_time + self._refresh_expires_in * 0.9
        )

    def token_expired(self):
        """
        Check if the token has expired.

        Returns:
            bool: True if the token has expired, False otherwise.
        """
        return time.time() > self._expiration_time

    def cursor_for(
        self, proxy_type: Type[ProxyClass] | str, **kwargs
    ) -> ProxyCursor[ProxyClass]:
        """Get a cursor for a given proxy type.

        Args:
            proxy_type: The type of the proxy. This can be provided as a string
                (the name of the proxy) or as the class itself.
            **kwargs: Additional arguments to pass to the cursor.

        Returns:
            ProxyCursor: The cursor for the proxy type.

        Example:
            client.cursor_for("Dataset")
            client.cursor_for(Dataset)
        """
        return self.registry_for(proxy_type)

    def request(
        self, method, endpoint, params=None, data=None, headers=None, json=None
    ):
        """
        Sends a request to the STELAR API.

        The main difference of this method with respect to `api_request` is that the
        endpoint is relative to the base URL, and it can include headers, as well as
        non-JSON data (e.g., form data).

        For example:
            response = c.request("GET", "api/v2/datasets")
            response = c.request("POST", "v2/dataset", json={"name": "my_dataset"})

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

        if self.token_expired():
            self.reauthenticate()

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
                self.reauthenticate()
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

        if self.token_expired():
            self.reauthenticate()

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
                self.reauthenticate()
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
        return self.api_request("PATCH", endpoint, params=params, json=json)

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

    def listapi(self, show_verbs=True):
        """Return a list of all available API endpoints."""
        specs = self.GET("../specs").json()
        paths = specs["paths"]

        L = []
        for path, methods in paths.items():
            if show_verbs:
                for method in methods:
                    L.append(f"{method.upper():<8} {path}")
            else:
                L.append(path)

        return L
