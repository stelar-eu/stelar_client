"""
The Client class is the main STELAR API client object.

The Client class primarily holds the API URL and user credentials needed to
access the API.
"""
from __future__ import annotations

from configparser import ConfigParser
from http.client import responses
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from requests.utils import get_auth_from_url, urldefragauth

from .admin import AdminAPI
from .catalog import CatalogAPI

# Import subAPIs modules
from .endpoints import APIEndpointsV1
from .knowgraph import KnowledgeGraphAPI
from .s3 import S3API
from .wfapi import WorkflowsAPI

if TYPE_CHECKING:
    from os import PathLike


class Client(WorkflowsAPI, CatalogAPI, KnowledgeGraphAPI, AdminAPI, S3API):
    """An SDK (client) for the STELAR API.

    Operation of the STELAR client requires three pieces of information:
    1. The base URL of the STELAR installation.
    2. A username for the user.
    3. Access and refresh tokens for the user. These tokens need to be refreshed periodically.

    The client can be initialized in four ways:
    1. By providing nothing. This is equivalent to specifying the context name "default".
    2. By providing a context name, which is looked up in the config file (see below).
    3. By providing a base URL, username, and password. The client will then authenticate
       the user and retrieve the access and refresh tokens. Note that, the password is
       not stored in the client or anywhere else.
    4. By providing a base URL, username, password, and a token JSON dictionary containing
       the access token, refresh token, and their expiration times.

    When options 3. or 4. above are used, when the tokens expire, the user must call
    either the method `reauthenticate(passwd)` providing the password, or calling method
    `reset_tokens(token_json)` with a new token JSON dictionary. Again, these tokens will
    eventually expire.

    By contrast, when the client is initialized with a context name, the client
    automatically reacquires the tokens when they expire, since the context config file
    contains the password needed to re-authenticate the user.

    By default the config file is located at $HOME/.stelar, but can be overridden by
    providing the 'config_file' keyword argument. The config file contains a
    collection of contexts, and is encoded in the INI format:

    | [default]
    | base_url=https://klms.example.com
    | username=joe
    | password=my!secret
    |
    | [admin]
    | base_url=https://klms.example.com
    | username=admin
    | password=very!secret

    The token_json dictionary is expected to have the following (indicative) structure:

    | {
    |     "access_token": "your_access_token",
    |     "refresh_token": "your_refresh_token",
    |     "expires_in": 600,
    |     "refresh_expires_in": 7200,
    | }


    Args:
        context (str): load the specified context from $HOME/.stelar (or
            the `config_file` path). If this is None, the default context is used.
            If a config file is not found, the base_url, username and password
            can be provided as keywords.

        base_url (str): The base URL to the STELAR installation. This URL contains only the
            hostname. Optionally, it may contain a user name and password, as in
            https://joe:joespassword@klms.example.com/
            The user name and password are only used if the keyword arguments 'username' and
            'password' are None.

        username (str): The user name to connect to for this client.
        password (str): The password to authenticate with.
        token_json (dict): A dictionary containing the access token, refresh token, and their expiration times.

        tls_verify (bool):  Verify the server TLS certificate. This setting takes precedence
            if given. If none, the default is to verify.

        config_file (PathLike): Path to the config file. If None, the default of "$HOME/.stelar" is
        used.
    """

    def __init__(
        self,
        context: str = None,
        *,
        base_url: str = None,
        username=None,
        password=None,
        token_json: dict = None,
        tls_verify=True,
        config_file: PathLike = None,
    ):
        # Validate base_url
        if context is None and base_url is None:
            context = "default"
        self._config_file = config_file
        self._context = context

        if not tls_verify:
            import urllib3

            urllib3.disable_warnings()

        if self._context is not None:  # init via context
            base_url, username, password = self.__from_context()
            token_json = self.authenticate(
                base_url, username=username, password=password, tls_verify=tls_verify
            )

        else:  # have base_url, get username and password
            uuser, upass = get_auth_from_url(base_url)
            if not username:
                username = uuser
            if not password:
                password = upass
            base_url = self.__normalize_base_url(base_url)
            if not token_json:
                token_json = self.authenticate(
                    base_url,
                    username=username,
                    password=password,
                    tls_verify=tls_verify,
                )

        self._username = username
        super().__init__(base_url, token_json, tls_verify)

    def reauthenticate(self, password: str = None):
        """Refresh the access token for this client.

        This method attempts to refresh the access token using the refresh token. If the
        refresh token is not available, or if it is also stale, the method will attempt to
        re-authenticate the user.

        Args:
            password (str): A password, which is used for username/password authentication.
                If not provided, the context mechanism is used.

        Raises:
            RuntimeError: If the refresh token is invalid or if re-authentication fails.
        """

        # First, try to use the refresh token.
        if self._refresh_token is not None:
            try:
                token_json = self.token_refresh(
                    self._base_url, self._refresh_token, self._tls_verify
                )
                self.reset_tokens(token_json)
                return
            except RuntimeError as e:
                # Suppress exception, proceed to refresh by re-authentication
                print(
                    "Refreshing token: an exception occurred using the refresh token:",
                    e,
                )
                pass

        if self._context:
            base_url, username, password = self.__from_context()
        else:
            username = self._username

        token_json = self.authenticate(
            self._base_url,
            username=username,
            password=password,
            tls_verify=self._tls_verify,
        )

        # Reset the client tokens
        self.reset_tokens(token_json)

    @classmethod
    def token_refresh(
        cls, base_url: str, refresh_token: str, tls_verify: bool = True
    ) -> dict:
        """
        Use the given refresh token to retrieve new access and refresh tokens.

        Args:
            base_url (str): The URL of the STELAR service
            refresh_token (str): The refresh token to use.
            tls_verify (bool): Whether to verify the server TLS certificate.

        Returns:
            A dict containing the access token, refresh token, token expiration times and the type of token
            (should be 'Bearer').

        Raises:
            RuntimeError: If authentication fails due to incorrect credentials or server issues.
        """

        req_data = {"refresh_token": refresh_token}
        req_url = urljoin(base_url, "/stelar/api/" + APIEndpointsV1.TOKEN_ISSUE)
        token_response = requests.put(
            url=req_url,
            json=req_data,
            headers={"Content-Type": "application/json"},
            verify=tls_verify,
        )
        status_code = token_response.status_code
        if status_code >= 500:  # Could be a message by the proxy, or a server error
            raise RuntimeError(
                "Could not authenticate user. The server is not available.",
                status_code,
                responses.get(status_code, "Unknown status code"),
                token_response.text,
            )
        token_json = token_response.json().get("result", None)
        success = token_response.json().get("success")

        if success and status_code in range(200, 300):
            return token_json
        else:
            raise RuntimeError(
                "Could not refresh the current token", status_code, token_json
            )

    @classmethod
    def authenticate(cls, base_url, username, password, tls_verify=True) -> dict:
        """
        Authenticates the user and retrieves access and refresh tokens.

        This method sends a POST request to the authentication endpoint using the provided
        username and password. Upon successful authentication, the method updates the token
        property and refreshes the token for all subAPI instances.

        Args:
            base_url (str): The URL of the STELAR service
            username (str): The username of the user.
            password (str): The password of the user.
            tls_verify (str): Whether to verify the server TLS certificate.

        Raises:
            RuntimeError: If authentication fails due to incorrect credentials or server issues.

        Returns:
            A dict containing the access token, refresh token, token expiration times and the type of token
            (should be 'Bearer').
        """

        auth_data = {"username": username, "password": password}
        req_url = urljoin(base_url, "/stelar/api/" + APIEndpointsV1.TOKEN_ISSUE)

        token_response = requests.post(
            url=req_url,
            json=auth_data,
            headers={"Content-Type": "application/json"},
            verify=tls_verify,
        )
        status_code = token_response.status_code
        if status_code >= 500:  # Could be a message by the proxy, or a server error
            raise RuntimeError(
                "Could not authenticate user. The server is not available.",
                status_code,
                responses.get(status_code, "Unknown status code"),
                token_response.text,
            )

        js = token_response.json()

        if status_code == 200:
            token_json = js["result"]
            return token_json
        else:
            raise RuntimeError(
                "Could not authenticate user.",
                status_code,
                js,
            )

    @staticmethod
    def __normalize_base_url(base_url):
        """
        Returns the base url for the STELAR service.

        This is computed from any partial URL, by appending
        the default path prefix '/stelar'. Also, any fragment
        or authentication info is removed.

        Args:
            base_url (str): The base URL to normalize.

        Returns:
            str: The API URL.
        """
        burl = urldefragauth(base_url)
        return urljoin(burl, "stelar")

    def __from_context(self):
        config_file = (
            self._config_file if self._config_file else Path.home() / ".stelar"
        )
        context = self._context
        c = ConfigParser()
        c.read(config_file)
        if not c.has_section(context):
            raise ValueError(f"Client context '{context}' does not exist")
        ctx = c[context]
        base_url = self.__normalize_base_url(ctx["base_url"])
        usr = ctx["username"]
        pwd = ctx["password"]
        self._ckan_apitoken = ctx.get("ckan_apitoken", None)
        return base_url, usr, pwd

    @property
    def DC(self):
        try:
            return self._ckan_client
        except AttributeError:
            from .backdoor import CKAN

            self._ckan_client = CKAN(client=self)
            return self._ckan_client

    __repr_classname = "stelar.client.Client"

    def __repr__(self):
        purl = urlparse(self._base_url)
        if self._username:
            netloc = f"{self._username}@{purl.netloc}"
        else:
            netloc = purl.netloc
        enhanced_url = urlunparse((purl.scheme, netloc, purl.path, "", "", ""))
        return f"{self.__repr_classname}({enhanced_url})"
