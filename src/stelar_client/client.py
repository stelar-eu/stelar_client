"""
The Client class is the main STELAR API client object.

The Client class primarily holds the API URL and user credentials needed to
access the API.
"""

from urllib.parse import urljoin, urlparse

class Client:
    """
    An SDK (client) for interacting with the STELAR API.

    Args:
        base_url (str): The base URL of the STELAR installation.
        token (str): The user token issued by the KLMS SSO service.

    Raises:
        ValueError: If the base_url is not a valid URL.
    """

    def __init__(self, base_url, token):
        # Ensure the base_url is valid
        if not self._is_valid_url(base_url):
            raise ValueError(f"Invalid base URL: {base_url}")

        # Normalize base_url
        self.base_url = self._normalize_base_url(base_url)
        self._token = token

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

    @property
    def api_url(self):
        """Constructs and returns the complete API URL."""
        return urljoin(self.base_url, "stelar")

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

   