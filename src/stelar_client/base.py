from urllib.parse import urlencode, urljoin

import requests


class BaseAPI:
    """Base class for all parts of the client API.

    Its main responsibility is to support API calls to the
    STELAR server. It also contains logic to manage the proxies.
    """

    def __init__(self, base_url, token, refresh_token, tls_verify=True):
        super().__init__()
        self._base_url = base_url
        self._api_url = base_url + "/api/"
        self._tls_verify = tls_verify
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

    def request(
        self, method, endpoint, params=None, data=None, headers=None, json=None
    ):
        """
        Sends a request to the STELAR API

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
        url = urljoin(self.api_url, endpoint)
        # If the URL does not contain a query, add parameters from 'params'
        if params:
            url = f"{url}?{urlencode(params)}"

        # Prepare headers, defaulting to Authorization if token is present and Content-Type
        default_headers = {
            "Content-Type": "application/json",
        }

        if self._token:
            default_headers["Authorization"] = f"Bearer {self._token}"

        if headers:
            default_headers.update(headers)

        turn = 0
        while turn < 2:
            # Make the request using the provided method, url, params, data, json, and headers
            response = requests.request(
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
                default_headers["Authorization"] = f"Bearer {self._token}"
                turn += 1
            else:
                break

        # Raise an exception for HTTP errors (4xx, 5xx responses)
        # response.raise_for_status()
        return response

    def api_request(self, method, endpoint, *, params=None, json=None):
        """Do an actual API call"""

        url = urljoin(self._api_url, endpoint)
        headers = {"Authorization": f"Bearer {self._token}"}
        if params is not None and "json" in params:
            json = params["json"]

        twice = 0
        while twice < 2:
            response = requests.request(
                method,
                url,
                params=params,
                json=json,
                headers=headers,
                verify=self._tls_verify,
            )
            if response.status_code == 401 and twice == 0:
                self.refresh_tokens()
                headers["Authorization"] = f"Bearer {self._token}"
                twice += 1
            else:
                break

        return response

    def GET(self, *endp, **params):
        endpoint = "/".join(endp)
        return self.api_request("GET", endpoint, params=params)

    def POST(self, *endp, **params):
        endpoint = "/".join(endp)
        return self.api_request("POST", endpoint, params=params)

    def PUT(self, *endp, **params):
        endpoint = "/".join(endp)
        return self.api_request("PUT", endpoint, params=params)

    def PATCH(self, *endp, **params):
        endpoint = "/".join(endp)
        return self.api_request("PATCH", endpoint, params=params)

    def DELETE(self, *endp, **params):
        endpoint = "/".join(endp)
        return self.api_request("DELETE", endpoint, params=params)
