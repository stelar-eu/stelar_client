"""
The Client class is the main STELAR API client object.

The Client class primarily holds the API URL and user credentials needed to
access the API.
"""
from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse, urlunparse
from requests.utils import get_auth_from_url, urldefragauth
from pathlib import Path
from configparser import ConfigParser
import requests

# Import subAPIs modules
from .endpoints import APIEndpointsV1
from .workflows import WorkflowsAPI
from .catalog import CatalogAPI
from .knowgraph import KnowledgeGraphAPI
from .admin import AdminAPI
from .s3 import S3API

if TYPE_CHECKING:
    from os import PathLike

class Client(WorkflowsAPI, CatalogAPI, KnowledgeGraphAPI, AdminAPI, S3API):
    """An SDK (client) for the STELAR API.
    
    The config file contains a collection of contexts, and is encoded in the
    INI format:    
    ```
    [default]
    base_url=https://klms.example.com
    username=joe
    password=my!secret

    [admin]
    base_url=https://klms.example.com
    username=admin
    password=very!secret
    ```

    Arguments:
        context (str): load the specified context from $HOME/.stelar (or 
        the 'stelar_config' path). If this is None, the default context is used.
        If a config file is not found, the base_url, username and password
        can be provided as keywords.

        base_url (str): The base URL to the STELAR installation. This URL contains only the
        hostname. Optionally, it may contain a user name and password, as in 
        https://joe:joespassword@klms.example.com/
        The user name and password are only used if the keyword arguments 'username' and 
        'password' are None.

        token (str): The user token issued by the KLMS SSO service, if available. If a token is
        provided, the username and password are ignored.

        username (str): The user name to authenticate as for this client.
        password (str): The password to authenticate with.

        tls_verify (bool):  Verify the server TLS certificate. This setting takes precedence
        if given. If none, the default is to verify.

        config_file (PathLike): Path to the config file. If None, the default of "$HOME/.stelar" is
        used.
    """

    def __init__(self, context: str=None, *, token=None, base_url:str =None, username=None, password=None, 
                 tls_verify=True, config_file: PathLike=None):
        # Validate base_url
        self._config_file = config_file
        self._context = context

        if not tls_verify:
            import urllib3
            urllib3.disable_warnings()

        if token is not None:  # direct provision of token
            if base_url is None:
                raise ValueError("Token is specified but base_url is missing")
            base_url = self.__normalize_base_url(base_url)
            refresh_token = None

        elif context is not None or base_url is None:  # init via context
            base_url, username, password = self.__from_context()
            token, refresh_token = self.authenticate(base_url, username=username, password=password, tls_verify=tls_verify)

        else: # have base_url, get username and password
            uuser, upass = get_auth_from_url(base_url)
            if not username:
                username = uuser
            if not password:
                password = upass
            base_url = self.__normalize_base_url(base_url)
            token, refresh_token = self.authenticate(base_url, username=username, password=password, tls_verify=tls_verify)

        self._username = username
        super().__init__(base_url, token, refresh_token, tls_verify)


        ####################################################################

    def __initialize_operators(self):
        ##  Instatiate the subAPIs as member variables of the client  ######
        self.workflows = self
        self.catalog = self
        self.knowledgegraph = self
        self.admin = self
        self.s3 = self


    @classmethod
    def authenticate(cls, base_url, username, password, tls_verify=True):
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
            ValueError: If either the username or password is empty.
            RuntimeError: If authentication fails due to incorrect credentials or server issues.

        Returns: 
            token, refresh_token: If authentication was successful, a OpenID token and refresh token
        """
       

        if username and password:
            auth_data = {
                "username": username,
                "password": password
            }
            req_url = urljoin(base_url, "/stelar/api"+APIEndpointsV1.TOKEN_ISSUE)

            token_response = requests.post(
                url=req_url, 
                json=auth_data, 
                headers={"Content-Type": "application/json"},
                verify=tls_verify)
            status_code = token_response.status_code
            token_json = token_response.json().get('result', None)
            success = token_response.json().get('success')
            
            if token_json and token_json['token'] and token_json['refresh_token'] and success and status_code == 200:
                token = token_json['token']
                refresh_token = token_json['refresh_token']

                return token, refresh_token

            else: 
                raise RuntimeError("Could not authenticate user. Check the provided credentials and verify the availability of the STELAR API.")
        else: 
            raise ValueError("Credentials were fully or partially empty!")


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
        config_file = self._config_file if self._config_file else Path.home()/".stelar"
        context = self._context if self._context else "default"
        c = ConfigParser()
        c.read(config_file)
        if not c.has_section(context):
            raise ValueError(f"Client context '{context}' does not exist")
        ctx = c[context]
        base_url = self.__normalize_base_url(ctx['base_url'])
        usr = ctx['username']
        pwd = ctx['password']
        return base_url, usr, pwd

    def __repr__(self):
        purl = urlparse(self._base_url)
        if self._username:
            netloc = f"{self._username}@{purl.netloc}"
        else:
            netloc = purl.netloc
        enhanced_url = urlunparse((purl.scheme, netloc, purl.path, '', '', ''))
        return f"{__name__}.{self.__class__.__qualname__}({enhanced_url})"
