"""
    Implement an accessor for CKAN API that bypasses the STELAR API.
    This is useful for debugging and testing.
"""

from stelar_client import Client
from urllib.parse import urljoin
import requests
import pprint, json


class ppdict(dict):
    def __repr__(self):
        #return pprint.saferepr(dict(self))
        return json.dumps(self, indent=4)


class CKAN:
    def __init__(self):
        self.client = Client('apitest')
        self.ckanapi = urljoin(self.client._base_url, "/dc/api/3/action/")
        self.headers = {
            'Authorization': self.client._ckan_apitoken,
            #'Content-Type': 'application/json',
        }
        
    def doreq(self, verb, endp, params, data, headers={}):
        url = urljoin(self.ckanapi, endp)
        r = requests.request(verb, url, params=params, data=data, headers=self.headers|headers)
        #r.raise_for_status()
        #return ppdict(r.json())
        return  r.json()

    def __getattr__(self, name):
        def ckan_call(data=None, **kwargs):
            return self.POST(name, data=kwargs)
        return ckan_call

    def GET(self, endp, params=None, headers={}, data={}):
        return self.doreq('GET', endp, params, data, headers)

    def POST(self, endp, params=None, headers={}, data={}):
        return self.doreq('POST', endp, params, data, headers)

    def PUT(self, endp, params=None, headers={}, data={}):
        return self.doreq('PUT', endp, params, data, headers)

    def DELETE(self, endp, params=None, headers={}, data={}):
        return self.doreq('DELETE', endp, params, data, headers)
                