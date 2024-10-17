"""The Client class is the main STELAR API client object.

The Client class is mainly a holder for the API URL and user credentials needed to
access the API.
"""

from urllib.parse import urljoin

class Client:
    """An SDK (client) for the STELAR API.

    Arguments:
        base_url: The base URL to the STELAR installation.
    """

    def __init__(self, base_url):
        # base_url must end with '/', enforce it
        if base_url[-1] != '/':
            base_url = base_url + '/'
        self.base_url = base_url

    @property
    def api_url(self):
        return urljoin(self.base_url , "stelar")
    
